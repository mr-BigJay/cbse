from app.models.command import CommandType
from app.models.device import Device, DeviceMode

CAPABILITY_LABELS = {
    "supported": "supported_and_ready",
    "permission": "requires_permission",
    "device_owner": "requires_device_owner",
    "user_confirm": "requires_user_confirmation",
    "unsupported": "unsupported",
}


def default_capabilities(mode: DeviceMode) -> dict[str, str]:
    base = {
        CommandType.STATUS.value: CAPABILITY_LABELS["supported"],
        CommandType.ALARM.value: CAPABILITY_LABELS["supported"],
        CommandType.LOCATE.value: CAPABILITY_LABELS["permission"],
        CommandType.LOCK.value: CAPABILITY_LABELS["permission"],
        CommandType.APP_LIST.value: CAPABILITY_LABELS["permission"],
        CommandType.SYNC_STATUS.value: CAPABILITY_LABELS["user_confirm"],
    }
    if mode == DeviceMode.managed:
        base[CommandType.LOCK.value] = CAPABILITY_LABELS["supported"]
        base[CommandType.APP_LIST.value] = CAPABILITY_LABELS["supported"]
        base[CommandType.LOCATE.value] = CAPABILITY_LABELS["supported"]
    return base


def merge_capabilities(device: Device) -> dict[str, str]:
    merged = default_capabilities(device.mode)
    if device.capabilities:
        merged.update(device.capabilities)
    return merged


def is_command_allowed(device: Device, cmd_type: CommandType) -> tuple[bool, str]:
    caps = merge_capabilities(device)
    state = caps.get(cmd_type.value, CAPABILITY_LABELS["unsupported"])
    if state == CAPABILITY_LABELS["unsupported"]:
        return False, state
    if state == CAPABILITY_LABELS["device_owner"] and device.mode != DeviceMode.managed:
        return False, state
    # Permission / user-confirm commands are queueable; the agent enforces Android gates.
    return True, state
