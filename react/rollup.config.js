import resolve from "@rollup/plugin-node-resolve";
import babel from "@rollup/plugin-babel";
import postcss from "rollup-plugin-postcss";

export default {
  input: "src/index.js",
  external: ["react", "react/jsx-runtime"],
  plugins: [
    resolve(),
    babel({
      babelHelpers: "bundled",
      presets: [["@babel/preset-react", { runtime: "automatic" }]],
      extensions: [".js", ".jsx"],
    }),
    postcss({ extract: "log.css" }),
  ],
  output: [
    { file: "dist/index.esm.js", format: "esm" },
    { file: "dist/index.cjs.js", format: "cjs" },
  ],
};
