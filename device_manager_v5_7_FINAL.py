"""Device Manager - v5.10 FINAL - Handle dual response formats"""

import logging
import asyncio
import threading
import time
from typing import Optional, Dict

_LOGGER = logging.getLogger(__name__)

class PersistentDeviceManager:
    """Singleton - v5.10 - Handle dual response formats from device"""

    _instances: Dict[str, 'PersistentDeviceManager'] = {}
    _lock = threading.Lock()

    def __new__(cls, device_id: str, local_key: str, ip_address: str, protocol_version: str = "3.4"):
        key = f"{device_id}_{ip_address}"
        with cls._lock:
            if key not in cls._instances:
                _LOGGER.info(f"🔧 Creating manager for {device_id}")
                instance = super().__new__(cls)
                cls._instances[key] = instance
                instance._init_basic(device_id, local_key, ip_address, protocol_version)
            return cls._instances[key]

    def _init_basic(self, device_id: str, local_key: str, ip_address: str, protocol_version: str):
        if hasattr(self, '_initialized'):
            return

        self._initialized = True
        self.device_id = device_id
        self.local_key = local_key
        self.ip_address = ip_address
        self.protocol_version = float(protocol_version)
        
        self._device = None
        self._device_lock = threading.Lock()
        self._device_initialized = False
        self._init_lock = asyncio.Lock()
        
        self._cached_status = {}
        self._cache_time = 0
        self._min_cache_interval = 5
        self._cache_validity = 10
        self._fetching = False
        
        self._error_914_count = 0
        self._timeout_count = 0
        self._consecutive_failures = 0
        self._last_keep_alive = 0
        self._last_complete_response = None
        
        self._status_timeout = 10.0
        self._set_timeout = 10.0
        
        _LOGGER.info(f"✅ Manager v5.10 initialized")
        _LOGGER.info(f"   Device: {device_id} @ {ip_address}")
        _LOGGER.info(f"   Handling dual response formats")

    async def _ensure_device_initialized(self):
        if self._device_initialized:
            return
        
        async with self._init_lock:
            if self._device_initialized:
                return
            
            _LOGGER.info(f"🔗 Initializing persistent connection")
            await asyncio.to_thread(self._create_device_sync)
            self._device_initialized = True

    def _create_device_sync(self):
        try:
            import tinytuya
            
            with self._device_lock:
                self._device = tinytuya.Device(
                    dev_id=self.device_id,
                    address=self.ip_address,
                    local_key=self.local_key,
                    version=self.protocol_version,
                )
                
                self._device.set_socketPersistent(True)
                self._device.set_socketNODELAY(False)
                self._device.heartbeat()
            
            self._error_914_count = 0
            self._timeout_count = 0
            self._consecutive_failures = 0
            _LOGGER.info(f"✅ Persistent connection established")
            
        except Exception as e:
            _LOGGER.error(f"❌ Connection failed: {type(e).__name__}: {e}")
            with self._device_lock:
                self._device = None

    def _reconnect_sync(self):
        _LOGGER.warning(f"🔄 Reconnecting to device...")
        with self._device_lock:
            self._device = None
        self._device_initialized = False
        self._create_device_sync()

    def _do_keep_alive_sync(self):
        try:
            with self._device_lock:
                if self._device and hasattr(self._device, 'heartbeat'):
                    self._device.heartbeat()
            _LOGGER.debug(f"💓 Keep-alive sent")
            self._last_keep_alive = time.time()
        except Exception as e:
            _LOGGER.debug(f"Keep-alive failed: {e}")

    async def _async_check_keep_alive(self):
        now = time.time()
        if now - self._last_keep_alive > 30:
            _LOGGER.debug(f"🔄 Keep-alive due")
            await asyncio.to_thread(self._do_keep_alive_sync)

    def _is_error_914(self, response: dict) -> bool:
        if not isinstance(response, dict):
            return False
        return response.get("Err") == "914" or "Check device key" in response.get("Error", "")

    def _normalize_response(self, data):
        """
        Handle dual response formats from device:
        
        Format 1 (Wrapped): {'protocol': 4, 'data': {'dps': {...}}, 'dps': {...}}
        Format 2 (Direct): {'dps': {...}}
        
        Always return {'dps': {...}} format
        """
        if not isinstance(data, dict):
            _LOGGER.error(f"❌ Response not a dict: {type(data).__name__}")
            return None
        
        # Already normalized format
        if "dps" in data and "protocol" not in data and "data" not in data:
            _LOGGER.debug(f"📨 Format 2 (Direct): dps has {len(data['dps'])} datapoints")
            return data
        
        # Wrapped format - need to unwrap
        if "protocol" in data and "data" in data and "dps" in data["data"]:
            unwrapped = data["data"]
            _LOGGER.debug(f"📨 Format 1 (Wrapped): unwrapped, dps has {len(unwrapped.get('dps', {}))} datapoints")
            return unwrapped
        
        # Format 1 but simpler structure
        if "dps" in data and isinstance(data["dps"], dict):
            _LOGGER.debug(f"📨 Format unclear but has dps: {len(data['dps'])} datapoints")
            return {"dps": data["dps"]}
        
        _LOGGER.error(f"❌ Cannot normalize response: {data}")
        return None

    def _validate_response(self, data):
        """Validate normalized response"""
        if data is None:
            return False
        
        if "dps" not in data:
            _LOGGER.error(f"❌ No 'dps' in normalized response")
            return False
        
        if not isinstance(data["dps"], dict):
            _LOGGER.error(f"❌ 'dps' is not dict: {type(data['dps'])}")
            return False
        
        if len(data["dps"]) == 0:
            _LOGGER.warning(f"⚠️ 'dps' is empty - device may be busy or not responding with all data")
            return True  # Still valid, just incomplete
        
        return True

    async def get_status(self) -> Optional[dict]:
        await self._ensure_device_initialized()
        
        if not self._device:
            _LOGGER.error(f"❌ Device not initialized")
            return self._cached_status if self._cached_status else {}

        now = time.time()
        cache_age = now - self._cache_time

        if self._cached_status and cache_age < self._cache_validity:
            _LOGGER.debug(f"📦 Cache hit (age: {cache_age:.1f}s, dps count: {len(self._cached_status.get('dps', {}))})")
            return self._cached_status

        if cache_age < self._min_cache_interval:
            _LOGGER.debug(f"⏳ Min interval not met")
            return self._cached_status

        if self._fetching:
            _LOGGER.debug(f"🔄 Already fetching")
            return self._cached_status

        max_retries = 2
        for attempt in range(max_retries):
            try:
                self._fetching = True
                _LOGGER.debug(f"📡 Fetching status (attempt {attempt + 1}/{max_retries})")
                
                def _get_device_status():
                    with self._device_lock:
                        if self._device:
                            return self._device.status()
                    return None
                
                raw_data = await asyncio.wait_for(
                    asyncio.to_thread(_get_device_status),
                    timeout=self._status_timeout
                )
                
                _LOGGER.debug(f"📨 Raw response: {raw_data}")
                
                if self._is_error_914(raw_data):
                    _LOGGER.error(f"❌ Error 914 - Device rejected request")
                    self._error_914_count += 1
                    if self._error_914_count >= 2:
                        await asyncio.to_thread(self._reconnect_sync)
                    return self._cached_status if self._cached_status else {}

                # Normalize response to handle both formats
                data = self._normalize_response(raw_data)
                
                if not self._validate_response(data):
                    if attempt < max_retries - 1:
                        _LOGGER.warning(f"⚠️ Invalid response, retrying...")
                        await asyncio.sleep(0.5)
                        continue
                    else:
                        _LOGGER.error(f"❌ Max retries with invalid response")
                        # Return last complete response if available
                        if self._last_complete_response:
                            _LOGGER.warning(f"⚠️ Using last complete response")
                            return self._last_complete_response
                        return self._cached_status if self._cached_status else {}

                # SUCCESS
                dps_count = len(data.get("dps", {}))
                self._error_914_count = 0
                self._timeout_count = 0
                self._consecutive_failures = 0
                
                # Save as last complete if has good data
                if dps_count > 1:  # More than just humidity
                    self._last_complete_response = data
                    _LOGGER.info(f"✅ Status fresh - complete response with {dps_count} dps")
                else:
                    _LOGGER.warning(f"⚠️ Status incomplete - only {dps_count} dps, using last complete")
                    if self._last_complete_response:
                        data = self._last_complete_response
                        _LOGGER.info(f"✅ Using last complete response with {len(data.get('dps', {}))} dps")
                
                self._cached_status = data
                self._cache_time = now
                return data

            except asyncio.TimeoutError:
                _LOGGER.error(f"❌ TIMEOUT after {self._status_timeout}s (attempt {attempt + 1}/{max_retries})")
                self._timeout_count += 1
                self._consecutive_failures += 1
                
                if self._consecutive_failures >= 3:
                    await asyncio.to_thread(self._reconnect_sync)
                    self._consecutive_failures = 0
                
                if attempt < max_retries - 1:
                    await asyncio.sleep(1)

            except Exception as e:
                _LOGGER.error(f"❌ EXCEPTION: {type(e).__name__}: {e} (attempt {attempt + 1}/{max_retries})")
                self._consecutive_failures += 1
                
                if self._consecutive_failures >= 3:
                    await asyncio.to_thread(self._reconnect_sync)
                    self._consecutive_failures = 0
                
                if attempt < max_retries - 1:
                    await asyncio.sleep(1)

            finally:
                self._fetching = False

        return self._cached_status if self._cached_status else {}

    async def set_value(self, dp: str, value) -> bool:
        await self._ensure_device_initialized()
        
        if not self._device:
            _LOGGER.error(f"❌ Device not initialized for set")
            return False

        await self._async_check_keep_alive()

        try:
            _LOGGER.debug(f"✏️ Setting DP {dp} = {value}")
            
            def _set_device_value():
                with self._device_lock:
                    if self._device:
                        return self._device.set_value(dp, value)
                return None
            
            response = await asyncio.wait_for(
                asyncio.to_thread(_set_device_value),
                timeout=self._set_timeout
            )
            
            if self._is_error_914(response):
                _LOGGER.error(f"❌ Error 914 on set: {response}")
                self._error_914_count += 1
                if self._error_914_count >= 2:
                    await asyncio.to_thread(self._reconnect_sync)
                return False

            self._error_914_count = 0
            self._timeout_count = 0
            self._consecutive_failures = 0
            self._cache_time = 0
            _LOGGER.info(f"✅ DP {dp} set to {value}")
            return True

        except asyncio.TimeoutError:
            _LOGGER.error(f"❌ SET TIMEOUT after {self._set_timeout}s")
            self._consecutive_failures += 1
            if self._consecutive_failures >= 3:
                await asyncio.to_thread(self._reconnect_sync)
                self._consecutive_failures = 0
            return False

        except Exception as e:
            _LOGGER.error(f"❌ SET EXCEPTION: {type(e).__name__}: {e}")
            self._consecutive_failures += 1
            if self._consecutive_failures >= 3:
                await asyncio.to_thread(self._reconnect_sync)
                self._consecutive_failures = 0
            return False
