import { Routes, Route } from "react-router-dom";

import Home from "./pages/Home";
import Medical from "./pages/Medical";
import Food from "./pages/Food";
import Shelter from "./pages/Shelter";
import Hazard from "./pages/Hazard";
import Messages from "./pages/Messages";

function App() {
  return (
    <Routes>
      <Route path="/" element={<Home />} />
      <Route path="/medical" element={<Medical />} />
      <Route path="/food" element={<Food />} />
      <Route path="/shelter" element={<Shelter />} />
      <Route path="/hazard" element={<Hazard />} />
      <Route path="/messages" element={<Messages />} />
    </Routes>
  );
}

export default App;