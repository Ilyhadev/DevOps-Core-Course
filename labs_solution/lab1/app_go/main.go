package main
// Took from lab01.md
import (
    "bufio"
    "encoding/json"
    "net/http"
    "os"
    "runtime"
    "strings"
    "time"
    "log"
    "strconv"
)


// Application metadata
const (
    ServiceName        = "devops-info-service"
    ServiceVersion     = "1.0.0"
    ServiceDescription = "DevOps course info service"
    FrameworkName      = "Go"
)

var startTime time.Time

// Same keys as Python app
type Service struct {
    Name        string `json:"name"`
    Version     string `json:"version"`
    Description string `json:"description"`
    Framework   string `json:"framework"`
}

type System struct {
    Hostname        string `json:"hostname"`
    Platform        string `json:"platform"`
    PlatformVersion string `json:"platform_version"`
    Architecture    string `json:"architecture"`
    CPUCount        int    `json:"cpu_count"`
    PythonVersion   string `json:"python_version"` // kept for structure parity
    GoVersion       string `json:"go_version,omitempty"`
}

type RuntimeInfo struct {
    UptimeSeconds int64  `json:"uptime_seconds"`
    UptimeHuman   string `json:"uptime_human"`
    CurrentTime   string `json:"current_time"`
    Timezone      string `json:"timezone"`
}

type RequestInfo struct {
    ClientIP  string `json:"client_ip"`
    UserAgent string `json:"user_agent"`
    Method    string `json:"method"`
    Path      string `json:"path"`
}

type Endpoint struct {
    Path        string `json:"path"`
    Method      string `json:"method"`
    Description string `json:"description"`
}

type FullPayload struct {
    Service   Service      `json:"service"`
    System    System       `json:"system"`
    Runtime   RuntimeInfo  `json:"runtime"`
    Request   RequestInfo  `json:"request"`
    Endpoints []Endpoint   `json:"endpoints"`
}

func getSystemInfo() System {
    host, _ := os.Hostname()
    pv := getOSPrettyName()
    if pv == "" {
        pv = "n/a"
    }
    return System{
        Hostname:        host,
        Platform:        strings.Title(runtime.GOOS),
        PlatformVersion: pv,
        Architecture:    runtime.GOARCH,
        CPUCount:        runtime.NumCPU(),
        PythonVersion:   "n/a", // Only go version is relevant here
        GoVersion:       runtime.Version(),
    }
}

func getOSPrettyName() string {
    f, err := os.Open("/etc/os-release")
    if err != nil {
        return ""
    }
    defer f.Close() // Close the file when done
    scanner := bufio.NewScanner(f)
    for scanner.Scan() {
        line := scanner.Text()
        if strings.HasPrefix(line, "PRETTY_NAME=") {
            val := strings.TrimPrefix(line, "PRETTY_NAME=")
            val = strings.Trim(val, `"`)
            return val
        }
    }
    return ""
}

func getUptime() (int64, string) {
    diff := time.Since(startTime)
    secs := int64(diff.Seconds())
    hours := secs / 3600
    mins := (secs % 3600) / 60
    human := ""
    if hours == 1 {
        human = fmtHoursMins(hours, mins)
    } else {
        human = fmtHoursMins(hours, mins)
    }
    return secs, human
}

func fmtHoursMins(h, m int64) string {
    hUnit := "hours"
    mUnit := "minutes"
	// A bit of basic pluralization
    if h == 1 {
        hUnit = "hour"
    }
    if m == 1 {
        mUnit = "minute"
    }
    return strings.TrimSpace(
        strings.Join([]string{fmtInt(h) + " " + hUnit + ",", fmtInt(m) + " " + mUnit}, " "),
    )
}

func fmtInt(v int64) string {
    return strconv.FormatInt(v, 10)
}

// Helper to obtain client IP from request, honouring X-Forwarded-For
func clientIP(r *http.Request) string {
    // respect X-Forwarded-For when present (common for proxies)
    xff := r.Header.Get("X-Forwarded-For")
    if xff != "" {
        // X-Forwarded-For may contain comma-separated list
        parts := strings.Split(xff, ",")
        return strings.TrimSpace(parts[0])
    }
    // Fallback to remote address (host:port)
    addr := r.RemoteAddr
    if idx := strings.LastIndex(addr, ":"); idx != -1 {
        return addr[:idx]
    }
    return addr
}

// Handler for GET /
func mainHandler(w http.ResponseWriter, r *http.Request) {
    secs, human := getUptime()
	// Build the full payload
    payload := FullPayload{
        Service: Service{
            Name:        ServiceName,
            Version:     ServiceVersion,
            Description: ServiceDescription,
            Framework:   FrameworkName,
        },
        System:  getSystemInfo(),
        Runtime: RuntimeInfo{UptimeSeconds: secs, UptimeHuman: human, CurrentTime: time.Now().UTC().Format(time.RFC3339), Timezone: "UTC"},
        Request: RequestInfo{ClientIP: clientIP(r), UserAgent: r.UserAgent(), Method: r.Method, Path: r.URL.Path},
        Endpoints: []Endpoint{
            {Path: "/", Method: "GET", Description: "Service information"},
            {Path: "/health", Method: "GET", Description: "Health check"},
        },
    }
	// Create enocoded JSON response
    w.Header().Set("Content-Type", "application/json")
    enc := json.NewEncoder(w)
    enc.SetIndent("", "  ")
    if err := enc.Encode(payload); err != nil {
        http.Error(w, "failed to encode payload", http.StatusInternalServerError)
    }
}

// Handler for GET /health
func healthHandler(w http.ResponseWriter, r *http.Request) {
    secs, _ := getUptime()
    health := map[string]interface{}{
        "status":       "healthy",
        "timestamp":    time.Now().UTC().Format(time.RFC3339),
        "uptime_seconds": secs,
    }
	// Create enocoded JSON response
    w.Header().Set("Content-Type", "application/json")
    enc := json.NewEncoder(w)
    _ = enc.Encode(health)
}

func main() {
    startTime = time.Now()
    http.HandleFunc("/", mainHandler)
    http.HandleFunc("/health", healthHandler)

    // Allow binding to a specific host/IP using HOST env variable (optional).
    // If HOST is empty or set to 0.0.0.0 we bind on all interfaces with :PORT.
    host := os.Getenv("HOST")
    if host == "" {
        host = "0.0.0.0"
    }

    port := os.Getenv("PORT")
    if port == "" {
        port = "8080"
    }

    var addr string
    if host == "0.0.0.0" {
        addr = ":" + port
    } else {
        addr = host + ":" + port
    }

    log.Printf("Starting %s on %s", ServiceName, addr)
    if err := http.ListenAndServe(addr, nil); err != nil {
        log.Fatalf("server failed: %v", err)
    }
}
