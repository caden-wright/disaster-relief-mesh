import { createContext, useContext, useEffect, useMemo, useState } from "react";
import { getHelpPointStatus } from "../api/helpPoint";

const HelpPointStatusContext = createContext(null);

export function HelpPointStatusProvider({ children, intervalMs = 5000 }) {
    const [status, setStatus] = useState(null);
    const [error, setError] = useState(false);

    useEffect(() => {
        let active = true;

        async function refresh() {
            try {
                const data = await getHelpPointStatus();

                if (active) {
                    setStatus(data);
                    setError(false);
                }
            } catch (err) {
                console.error("Help Point status check failed:", err);

                if (active) {
                    setStatus(null);
                    setError(true);
                }
            }
        }

        refresh();

        const interval = setInterval(refresh, intervalMs);

        return () => {
            active = false;
            clearInterval(interval);
        };
    }, [intervalMs]);

    const value = useMemo(() => {
        const backendOnline = !error && status !== null;
        const meshOnline =
            backendOnline && status.mesh_connected === true;

        return {
            status,
            error,
            backendOnline,
            meshOnline,
            queueDepth: status?.queue_depth ?? 0
        };
    }, [status, error]);

    return (
        <HelpPointStatusContext.Provider value={value}>
            {children}
        </HelpPointStatusContext.Provider>
    );
}

export function useHelpPointStatus() {
    const context = useContext(HelpPointStatusContext);

    if (!context) {
        throw new Error(
            "useHelpPointStatus must be used inside HelpPointStatusProvider"
        );
    }

    return context;
}