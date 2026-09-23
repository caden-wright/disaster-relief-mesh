import { NavLink } from "react-router-dom";
import "./AppHeader.css";
import { useHelpPointStatus } from "../context/HelpPointStatusContext";

function AppHeader() {
    const {
        status,
        backendOnline,
        meshOnline,
        queueDepth
    } = useHelpPointStatus();

    let statusClass = "header-status";
    let statusLabel = "Connecting...";
    let statusDetail = "Checking Help Point";

    if (!backendOnline) {
        statusClass += " header-status-offline";
        statusLabel = "Help Point Offline";
        statusDetail = "Local service unavailable";
    } else if (!meshOnline) {
        statusClass += " header-status-warning";
        statusLabel = "Mesh Offline";
        statusDetail =
            queueDepth > 0
                ? `${queueDepth} queued ${queueDepth === 1 ? "message" : "messages"}`
                : "Requests will be queued";
    } else {
        statusLabel = "Mesh Online";
        statusDetail =
            queueDepth > 0
                ? `${queueDepth} pending ${queueDepth === 1 ? "message" : "messages"}`
                : `Help Point ${status?.help_point_id ?? ""}`;
    }

    return (
        <header className="app-header">

            <div className="header-content">

                <NavLink to="/" className="brand">
                    <div className="brand-icon">
                        M
                    </div>

                    <div className="brand-text">
                        <span className="brand-name">
                            MeshAid
                        </span>

                        <span className="brand-subtitle">
                            Disaster Relief Help Point
                        </span>
                    </div>
                </NavLink>

                <div className={statusClass}>
                    <span className="status-dot"></span>

                    <div>
                        <span className="status-label">
                            {statusLabel}
                        </span>

                        <span className="status-detail">
                            {statusDetail}
                        </span>
                    </div>
                </div>

            </div>

            <nav className="app-nav">

                <NavLink
                    to="/"
                    end
                    className={({ isActive }) =>
                        isActive ? "active" : ""
                    }
                >
                    Home
                </NavLink>

                <NavLink
                    to="/check-in"
                    className={({ isActive }) =>
                        isActive ? "active" : ""
                    }
                >
                    Check-In
                </NavLink>

                <NavLink
                    to="/medical"
                    className={({ isActive }) =>
                        isActive ? "active" : ""
                    }
                >
                    Medical
                </NavLink>

                <NavLink
                    to="/resources"
                    className={({ isActive }) =>
                        isActive ? "active" : ""
                    }
                >
                    Resources
                </NavLink>

                <NavLink
                    to="/messages"
                    className={({ isActive }) =>
                        isActive ? "active" : ""
                    }
                >
                    Messages
                </NavLink>

            </nav>

        </header>
    );
}

export default AppHeader;