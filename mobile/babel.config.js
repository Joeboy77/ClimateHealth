module.exports = function (api) {
  api.cache(true);
  return {
    presets: ["babel-preset-expo"],
    // Reanimated 4 runs animations on the UI thread through worklets. This plugin must
    // be last, and without it every animation silently falls back to the JS thread.
    plugins: ["react-native-worklets/plugin"],
  };
};
