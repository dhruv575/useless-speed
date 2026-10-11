import { prepareRoute } from "./prepare";
import { compare } from "./simulation";
import type { Sources } from "./types";
let sources: Sources;
self.onmessage = ({ data }) => {
  try {
    if (data.type === "init") {
      sources = data.sources;
      self.postMessage({ type: "ready" });
      return;
    }
    const route = prepareRoute(data.raw, sources, data.hour);
    const comparison = compare(route, data.overspeed);
    self.postMessage({ type: "result", id: data.id, route, comparison });
  } catch (error) {
    self.postMessage({
      type: "error",
      id: data.id,
      error:
        error instanceof Error
          ? error.message
          : "The model could not calculate this route.",
    });
  }
};
