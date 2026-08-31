import { Link, useLocation } from "react-router-dom";
import "./AppHeader.css";
import Icon from "./Icon";

function AppHeader() {
    const location = useLocation();

    return (
        <header className="app-header">
            <div className="header-content">

                <Link to="/" className="brand">
                    <div className="brand-icon">
                        <Icon name="medical" size={26} />
                    </div>

                    <div className="brand-text">
                        <span className="brand-name">ReliefMesh</span>
                        <span className="brand-subtitle">
                            Disaster Relief Network
                        </span>
                    </div>
                </Link>

                <div
                    className="header-status"
                    role="status"
                    aria-label="Help Point connected"
                >
                    <span className="status-dot"></span>
                    <div>
                        <span className="status-label">Help Point Online</span>
                        <span className="status-detail">
                            Local Station Connected
                        </span>
                    </div>
                </div>

            </div>

            {location.pathname !== "/" && (
                <nav
                    className="app-nav"
                    aria-label="Primary navigation"
                >

                    <Link
                        to="/"
                        className={location.pathname === "/" ? "active" : ""}
                    >
                        Home
                    </Link>

                    <Link
                        to="/check-in"
                        className={
                            location.pathname === "/check-in"
                                ? "active"
                                : ""
                        }
                    >
                        Check-In
                    </Link>

                    <Link
                        to="/medical"
                        className={
                            location.pathname === "/medical"
                                ? "active"
                                : ""
                        }
                    >
                        Medical
                    </Link>

                    <Link
                        to="/resources"
                        className={
                            location.pathname === "/resources"
                                ? "active"
                                : ""
                        }
                    >
                        Resources
                    </Link>

                    <Link
                        to="/messages"
                        className={
                            location.pathname === "/messages"
                                ? "active"
                                : ""
                        }
                    >
                        Messages
                    </Link>

                </nav>
            )}
        </header>
    );
}

export default AppHeader;