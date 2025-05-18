const path = require("path")
const HtmlWebpackPlugin = require("html-webpack-plugin")
const CopyPlugin = require("copy-webpack-plugin")
const webpack = require("webpack")
const dotenv = require("dotenv")

// Load env variables from .env file
const env = dotenv.config().parsed || {}

// Convert to format webpack.DefinePlugin expects
const envKeys = Object.keys(env).reduce((acc, key) => {
  acc[`process.env.${key}`] = JSON.stringify(env[key])
  return acc
}, {})

module.exports = {
  entry: "./src/popup.tsx",
  output: {
    path: path.resolve(__dirname, "dist"),
    filename: "popup.js"
  },
  resolve: {
    extensions: [".ts", ".tsx", ".js"]
  },
  module: {
    rules: [
      {
        test: /\.tsx?$/,
        use: "ts-loader",
        exclude: /node_modules/
      }
    ]
  },
  plugins: [
    new HtmlWebpackPlugin({
      template: "./src/popup.html",
      filename: "popup.html"
    }),
    new CopyPlugin({
      patterns: [{ from: "src/manifest.json", to: "." }]
    }),
    new webpack.DefinePlugin(envKeys) // ✅ Inject your .env values here
  ]
}
