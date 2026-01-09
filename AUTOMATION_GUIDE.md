# VAJRA Automation - Bug Bounty Pipeline

## 🎯 Overview
Professional bug bounty reconnaissance automation tool with parallel execution, multi-target support, and comprehensive reporting.

## ✨ Features Implemented

### 1. ✅ Subdomain Enumeration Tools
**Replaced Amass with:**
- **Subfinder** - Fast passive subdomain discovery
- **theHarvester** - Email, subdomain, and IP harvesting
- **Chaos** - ProjectDiscovery's chaos dataset
- **Sublist3r** - Python-based subdomain enumerator

**All tools run in PARALLEL for maximum speed!**

### 2. ✅ Smart Subdomain Merging
- Automatically combines results from all tools
- **Deduplicates** entries (case-insensitive)
- Outputs to **`subdomains.txt`** for next stage
- Shows total unique subdomains found

### 3. ✅ Parallel Execution
- Runs subdomain tools **simultaneously**
- Uses `ThreadPoolExecutor` with configurable workers
- **50%+ faster** than sequential execution
- Real-time status updates for each tool

### 4. ✅ Tool Configuration Panel
**Configurable parameters:**
- Enable/Disable Chaos and Sublist3r
- Parallel vs Sequential execution
- HTTPX threads (10-200)
- Nmap top ports (100-10000)
- theHarvester sources and limits
- Subfinder timeout settings

### 5. ✅ Progress Estimation
- **Real-time progress bar** (0-100%)
- Current step indication
- Estimated completion time
- Live statistics dashboard

### 6. ✅ Results Preview
**Live Statistics Panel:**
- 🎯 Total targets scanned
- 🌐 Subdomains discovered
- 📡 Live hosts found
- ⏱️ Elapsed time

**Per-Tool Results:**
- Shows completion status for each tool
- Displays subdomain count after enumeration
- Shows live hosts after HTTPX probing
- Success/failure indicators

### 7. ✅ Multiple Target Support
**Supports:**
- Single domain: `example.com`
- Multiple domains from file: `/path/to/domains.txt`
- Batch processing with progress tracking
- Individual reports per target

### 8. ✅ Notification System
- Desktop notifications via VAJRA notification manager
- Alerts on completion: "🎉 Automation complete! Scanned X targets in Ys"
- Integration with existing notification panel
- Shows final statistics

### 9. ✅ JSON Export for Reporting
**Each scan generates `automation_results.json` with:**
```json
{
  "target": "example.com",
  "scan_date": "2026-01-09T15:58:25",
  "statistics": {
    "subdomains_found": 250,
    "live_hosts": 38
  },
  "files": {
    "subdomains": "path/to/subdomains.txt",
    "live_hosts": "path/to/httpx_probed.txt",
    "nmap_scan": "path/to/nmap_scan.xml"
  }
}
```

## 🔧 Pipeline Workflow

```
1. 🔍 Whois Lookup
   └─> Domain information gathering

2. 🌐 Subdomain Enumeration (PARALLEL)
   ├─> Subfinder
   ├─> theHarvester
   ├─> Chaos (optional)
   └─> Sublist3r (optional)
   └─> Merge → subdomains.txt (deduplicated)

3. 📡 HTTP Probing
   └─> HTTPX scans all subdomains
   └─> Outputs live hosts

4. 🔍 Port Scanning
   └─> Nmap scans live hosts
   └─> Top N ports (configurable)

5. 📝 Report Generation
   └─> Creates HTML report
   └─> Exports JSON results
```

## 🎨 UI Features

### Control Panel
- **Target input** with file/domain support
- **Configuration panel** with all tool settings
- **START/SKIP/STOP buttons** for control
- Dependency checker before execution

### Status Tracking
- **Progress bar** with percentage
- **Pipeline status** for each step:
  - ⏳ Pending
  - 🔄 Running
  - ✅ Completed
  - ⏭️ Skipped
  - ❌ Error
  - ⛔ Terminated

### Live Statistics
- Real-time metrics
- Color-coded status
- Formatted output with icons

### Output Panel
- Streaming command output
- Color-coded messages
- HTML formatting
- Copy button included

## 📋 Required Tools

Install these tools before using automation:

```bash
# Core tools (required)
sudo apt install whois nmap

# Go tools
go install -v github.com/projectdiscovery/subfinder/v2/cmd/subfinder@latest
go install -v github.com/projectdiscovery/httpx/cmd/httpx@latest
go install -v github.com/projectdiscovery/chaos-client/cmd/chaos@latest

# Python tools
pip install theHarvester
pip install sublist3r
```

## 🚀 Usage

1. Open **Automation** tool from sidebar
2. Enter target(s):
   - Single: `example.com`
   - Multiple: `/path/to/targets.txt`
3. Configure tool settings (optional)
4. Click **START AUTOMATION**
5. Monitor progress in real-time
6. Review results and reports

## ⚙️ Configuration Options

| Setting | Default | Range | Description |
|---------|---------|-------|-------------|
| Parallel Execution | ✅ Enabled | - | Run subdomain tools simultaneously |
| Enable Chaos | ✅ Enabled | - | Use ProjectDiscovery chaos dataset |
| Enable Sublist3r | ✅ Enabled | - | Use Sublist3r enumeration |
| HTTPX Threads | 50 | 10-200 | Concurrent HTTP probes |
| Nmap Top Ports | 1000 | 100-10000 | Number of ports to scan |

## 📊 Output Files

For each target, the following structure is created:

```
Target-example.com/
├── Logs/
│   ├── whois.txt
│   ├── subfinder.out
│   ├── theharvester.out
│   ├── chaos.out
│   ├── sublist3r.out
│   ├── httpx.out
│   └── nmap.out
├── Subdomains/
│   ├── subfinder.txt
│   ├── theharvester.txt
│   ├── chaos.txt
│   ├── sublist3r.txt
│   └── subdomains.txt (merged & deduplicated)
├── Probed/
│   └── httpx_probed.txt
├── Scans/
│   ├── nmap_scan.xml
│   ├── nmap_scan.nmap
│   └── nmap_scan.gnmap
├── automation_results.json
└── Report.html
```

## 🎯 Bug Bounty Optimized

This automation is specifically designed for bug bounty workflows:

✅ Fast parallel enumeration  
✅ Comprehensive subdomain discovery  
✅ Live host validation before scanning  
✅ Configurable for different scenarios  
✅ Multiple targets for program-wide recon  
✅ JSON output for custom reporting  
✅ Integration with existing VAJRA tools  

## 🔄 Workflow Tips

**Quick Scan (Fast)**
- Enable only Subfinder
- Disable Chaos & Sublist3r
- Reduce HTTPX threads to 30
- Scan top 100 ports

**Comprehensive Scan (Thorough)**
- Enable all subdomain tools
- Parallel execution ON
- HTTPX threads: 100
- Scan top 3000 ports

**Large Programs (Multiple Targets)**
- Use targets file with all domains
- Enable all tools
- Let it run overnight
- Review results in morning

## 📈 Performance

**Example scan (example.com):**
- Subdomain tools: ~2-3 minutes (parallel)
- HTTPX probing: ~1-2 minutes
- Nmap scanning: ~5-10 minutes
- **Total: ~10-15 minutes**

**vs Sequential approach: ~25-30 minutes**

## 🎉 Success Indicators

When automation completes successfully, you'll see:
1. ✅ All steps marked as "Completed"
2. 🎯 Statistics showing discovered assets
3. 📝 Reports generated in target directory
4. 🔔 Desktop notification
5. 💾 JSON results exported

---

**Made with ❤️ for Bug Bounty Hunters**

*Last Updated: 2026-01-09*
