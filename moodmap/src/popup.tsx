import React, { useEffect, useState } from "react"
import ReactDOM from "react-dom/client"

declare const process: {
    env: {
      WEATHER_API: string
    }
  }

const App = () => {
  const [weather, setWeather] = useState("Loading…")
  const [error, setError] = useState("")
  const [debug, setDebug] = useState(localStorage.getItem("debug") === "true")

  useEffect(() => {
    chrome.tabs.query({ active: true, currentWindow: true }, (tabs: chrome.tabs.Tab[]) => {
      const url = tabs[0]?.url || ""
      let lat = "", lng = ""

      const m1 = url.match(/!3d([-.\d]+)!4d([-.\d]+)/)
      if (m1) {
        lat = m1[1]
        lng = m1[2]
        if (debug) console.log("Matched !3d/!4d:", lat, lng)
      } else {
        const m2 = url.match(/@([-.\d]+),([-.\d]+)/)
        if (m2) {
          lat = m2[1]
          lng = m2[2]
          if (debug) console.log("Matched @lat,lng:", lat, lng)
        }
      }

      if (!lat || !lng) {
        const msg = `No coordinates found in URL: ${url}`
        if (debug) console.warn(msg)
        setError("No coordinates found in URL")
        return
      }

      //const apiUrl = `https://pocmior.pythonanywhere.com/weather?lat=${lat}&long=${lng}`
      const baseUrl = process.env.WEATHER_API
      const apiUrl = `${baseUrl}?lat=${lat}&long=${lng}`
      if (debug) console.log("Fetching weather from:", apiUrl)

      fetch(apiUrl)
        .then((res) => res.json())
        .then((data) => {
          if (debug) console.log("Weather API response:", data)
          setWeather(data.weather_desc)
        })
        .catch((err) => {
          if (debug) console.error("Fetch failed:", err)
          setError("Weather fetch failed")
        })
    })
  }, [debug])

  return (
    <div style={{ padding: 16, minWidth: 220, fontFamily: "sans-serif" }}>
      <h3>Weather at location:</h3>
      {error ? <p style={{ color: "red" }}>{error}</p> : <p>{weather}</p>}

      {/* Only show checkbox if debug mode is enabled */}
      {localStorage.getItem("debug") === "true" && (
        <label>
          <input
            type="checkbox"
            checked={debug}
            onChange={(e) => {
              const value = e.target.checked
              localStorage.setItem("debug", value ? "true" : "false")
              setDebug(value)
            }}
          />
          Debug
        </label>
      )}
    </div>
  )
}

const root = ReactDOM.createRoot(document.getElementById("root")!)
root.render(<App />)
