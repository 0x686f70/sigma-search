# Define Sigma to Stellar Cyber field mappings
SIGMA_TO_STELLAR_FIELDS = {
    "CommandLine": "event_data.CommandLine",
    "Image": "event_data.Image",
    "ParentImage": "event_data.ParentImage",
    "ParentCommandLine": "event_data.ParentCommandLine",
    "ProcessId": "event_data.ProcessId",
    "ParentProcessId": "event_data.ParentProcessId",
    "TargetImage": "event_data.TargetImage",
    "GrantedAccess": "event_data.GrantedAccess",
    "CallTrace": "event_data.CallTrace",
    "TargetObject": "event_data.TargetObject",
    "Details": "event_data.Details",
    "EventType": "event_data.EventType",
    "PipeName": "event_data.PipeName",
    "DestinationHostname": "event_data.DestinationHostname",
    "Hashes": "event_data.Hashes",
    "Signature": "event_data.Signature",
    "ScriptBlockText": "event_data.ScriptBlockText",
    "RuleName": "event_data.RuleName",
    "User": "event_data.User",
    "LogonId": "event_data.LogonId",
    "EventID": "event_id",
    "ContextInfo": "event_data.ContextInfo",
    "Payload": "event_data.Payload",
    "ImageLoaded": "event_data.ImageLoaded",
    "OriginalFileName": "event_data.OriginalFileName",
    # Add missing field mappings for the example
    "SubjectUserSid": "event_data.SubjectUserSid",
    "LogonType": "event_data.LogonType",
    "LogonProcessName": "event_data.LogonProcessName",
    "KeyLength": "event_data.KeyLength",
    "TargetUserName": "event_data.TargetUserName",
    "ImagePath": "event_data.ImagePath",
    "SourceName": "event_data.SourceName",
    "Provider_Name": "source_name",
    "ServiceName": "event_data.ServiceName",
    
    # IIS Event Log Fields
    "date": "event_data.date",
    "time": "event_data.time",
    "c-ip": "event_data.c-ip",
    "cs-username": "event_data.cs-username",
    "s-sitename": "event_data.s-sitename",
    "s-computername": "event_data.s-computername",
    "s-ip": "event_data.s-ip",
    "s-port": "event_data.s-port",
    "cs-method": "event_data.cs-method",
    "cs-uri-stem": "event_data.cs-uri-stem",
    "cs-uri-query": "event_data.cs-uri-query",
    "sc-status": "event_data.sc-status",
    "sc-substatus": "event_data.sc-substatus",
    "sc-win32-status": "event_data.sc-win32-status",
    "sc-bytes": "event_data.sc-bytes",
    "cs-bytes": "event_data.cs-bytes",
    "time-taken": "event_data.time-taken",
    "cs-version": "event_data.cs-version",
    "cs-host": "event_data.cs-host",
    "csUser-Agent": "event_data.csUser-Agent",
    "csCookie": "event_data.csCookie",
    "cs-referer": "event_data.csReferer",
    "csReferer": "event_data.csReferer",
    "EnabledFieldsFlags": "event_data.EnabledFieldsFlags"
}

# Create reverse mapping for display purposes (Stellar field -> Display name)
STELLAR_TO_DISPLAY_NAME = {}
for sigma_field, stellar_field in SIGMA_TO_STELLAR_FIELDS.items():
    # Use the Sigma field name as display name (more readable)
    STELLAR_TO_DISPLAY_NAME[stellar_field] = sigma_field

# Add custom display names for better readability
CUSTOM_DISPLAY_NAMES = {
    "event_data.c-ip": "Client IP",
    "event_data.cs-username": "Client Username",
    "event_data.s-sitename": "Site Name",
    "event_data.s-computername": "Server Name",
    "event_data.s-ip": "Server IP",
    "event_data.s-port": "Server Port",
    "event_data.cs-method": "HTTP Method",
    "event_data.cs-uri-stem": "URI Path",
    "event_data.cs-uri-query": "Query String",
    "event_data.sc-status": "HTTP Status",
    "event_data.sc-substatus": "HTTP Substatus",
    "event_data.sc-win32-status": "Win32 Status",
    "event_data.sc-bytes": "Bytes Sent",
    "event_data.cs-bytes": "Bytes Received",
    "event_data.time-taken": "Time Taken (ms)",
    "event_data.cs-version": "HTTP Version",
    "event_data.cs-host": "Host Header",
    "event_data.csUser-Agent": "User Agent",
    "event_data.csCookie": "Cookie",
    "event_data.csReferer": "Referer",
    "event_data.date": "Date",
    "event_data.time": "Time"
}

# Merge custom display names
STELLAR_TO_DISPLAY_NAME.update(CUSTOM_DISPLAY_NAMES)


def get_field_display_name(field_path: str) -> str:
    """
    Get a human-readable display name for a field path.
    
    Args:
        field_path: The field path (e.g., 'event_data.cs-method')
        
    Returns:
        Human-readable display name
    """
    # Check if we have a custom display name
    if field_path in STELLAR_TO_DISPLAY_NAME:
        return STELLAR_TO_DISPLAY_NAME[field_path]
    
    # If not, try to format the field name nicely
    if field_path.startswith('event_data.'):
        field_name = field_path.replace('event_data.', '')
        # Handle hyphenated names (IIS fields)
        if '-' in field_name:
            parts = field_name.split('-')
            return ' '.join(part.capitalize() for part in parts)
        # Handle camelCase
        return field_name
    
    return field_path


# Define Sigma operator mappings
SIGMA_OP_MAP = {
    "contains": "contains",
    "startswith": "starts with",
    "endswith": "ends with",
    "equals": "is",
    "is": "is",
    "all": "is",
    "in": "is in lookup",
    "not in": "is not in lookup",
    "matches": "matches",
    "re": "matches",
    "regex": "matches",
    "startswith~": "starts with",
    "endswith~": "ends with",
    "contains~": "contains",
    "cidr": "is in cidr",
    "not": "is not",
    "not contains": "is not contains",
    "exists": "exists",
}
