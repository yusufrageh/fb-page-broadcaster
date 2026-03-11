import { BrowserRouter, Routes, Route } from "react-router-dom";
import Layout from "./components/Layout";
import Settings from "./pages/Settings";
import Pages from "./pages/Pages";
import Compose from "./pages/Compose";
import Broadcast from "./pages/Broadcast";
import History from "./pages/History";

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route element={<Layout />}>
          <Route path="/" element={<Settings />} />
          <Route path="/pages" element={<Pages />} />
          <Route path="/compose" element={<Compose />} />
          <Route path="/broadcast" element={<Broadcast />} />
          <Route path="/history" element={<History />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}
