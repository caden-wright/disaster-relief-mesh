import { Routes, Route } from "react-router-dom";

import AppHeader from "./components/AppHeader";

import Home from "./pages/Home";
import CheckIn from "./pages/CheckIn";
import Medical from "./pages/Medical";
import Resources from "./pages/Resources";
import Messages from "./pages/Messages";

function App() {
    return (
        <>
            <AppHeader />

            <main>
                <Routes>

                    <Route
                        path="/"
                        element={<Home />}
                    />

                    <Route
                        path="/check-in"
                        element={<CheckIn />}
                    />

                    <Route
                        path="/medical"
                        element={<Medical />}
                    />

                    <Route
                        path="/resources"
                        element={<Resources />}
                    />

                    <Route
                        path="/messages"
                        element={<Messages />}
                    />

                </Routes>
            </main>
        </>
    );
}

export default App;