# Performance Optimization Guide

## Startup Time Analysis

Current startup time: **~10 seconds**

### Breakdown:
- Flask app creation: 0.00s
- Directory setup: 0.00s
- **Rules loading: 10.30s** ⚠️ (BOTTLENECK)
- Deployment manager: 0.00s
- Route initialization: 0.01s

### Root Cause:
Loading 4,151 Sigma rules at startup:
- 3,053 standard rules
- 408 emerging-threats rules
- 126 threat-hunting rules
- 564 custom rules

Each rule requires:
1. File system scan
2. YAML parsing
3. Validation
4. Memory storage

## Optimization Options

### Option 1: Lazy Loading (Recommended for Development)
**Pros:**
- Instant startup (~0.5s)
- Load rules on first request
- Better development experience

**Cons:**
- First request will be slower
- Complexity in code

### Option 2: Parallel Loading
**Pros:**
- Faster loading (3-5s instead of 10s)
- All rules available immediately

**Cons:**
- More CPU usage
- More complex error handling

### Option 3: Rule Caching
**Pros:**
- Only load once, cache to disk
- Subsequent starts are instant

**Cons:**
- Need cache invalidation logic
- Disk space usage

### Option 4: Selective Loading
**Pros:**
- Only load rules you need
- Much faster startup

**Cons:**
- Need configuration
- May miss some rules

## Current Implementation

The app loads ALL rules at startup for immediate availability. This is good for production but slow for development.

## Recommendations

### For Development:
1. Use hot reload (already enabled)
2. Keep app running, don't restart
3. Consider lazy loading if needed

### For Production:
1. Current approach is fine (load once at startup)
2. Consider caching for faster restarts
3. Use process managers (gunicorn, uwsgi) that keep app in memory

## Quick Wins

### 1. Reduce Rule Set (Temporary)
Comment out rule directories you don't need in `app/rule_loader.py`:

```python
additional_rule_dirs = [
    # 'rules-emerging-threats',  # Comment out if not needed
    # 'rules-threat-hunting',
    # 'rules-compliance',
    # 'rules-dfir',
]
```

### 2. Use SSD
If rules are on HDD, move to SSD for 2-3x faster file I/O.

### 3. Increase File System Cache
Windows: Ensure enough RAM for file system cache.

## Monitoring

Check startup time with:
```bash
python -c "import time; start=time.time(); from app import create_application; app=create_application(); print(f'Startup: {time.time()-start:.2f}s')"
```
