const { defineConfig } = require("@vue/cli-service");
module.exports = defineConfig({
  transpileDependencies: true,
  assetsDir: 'static',
  devServer: {
    port: 9090,
  },
  outputDir: 'dist',
  configureWebpack: {
    devtool: 'inline-source-map',
    optimization: {
      splitChunks: {
        minSize: 100000,
        maxSize: 200000,
      },
    },
  },
})
