def validIpAddress(address):
    parts = address.split(".")
    if len(parts) != 4:
        return False
    try:
        for item in parts:
            if not 0 <= int(item) <= 255:
                return False
    except:
        return False
    
    return True

def validPort(port):
    
    try:
        if not 0 <= int(port) <= 65535:
            return False
    except:
        return False
    
    return True