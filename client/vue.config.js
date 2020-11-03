module.exports = {
  css: {
    loaderOptions: {
      sass: {
        prependData: `@import "@/assets/custom.scss";`
      }
    }
  }
  // publicPath: process.env.NODE_ENV === 'production'
  //   ? '/SenVis/'
  //   : '/'
};
