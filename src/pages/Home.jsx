import { Link } from "react-router-dom";
import "./Home.css";
import Icon from "../components/Icon";
import { useHelpPointStatus } from "../context/HelpPointStatusContext";

function Home() {
    const {
        backendOnline,
        meshOnline,
        queueDepth
    } = useHelpPointStatus();

    return (
        <div className="home-container">

            <section className="home-intro">
                <span className="eyebrow">
                    HELP POINT TERMINAL
                </span>

                <h1>Emergency Assistance</h1>

                <p>
                    Submit a status update or request assistance through
                    the local disaster relief mesh network.
                </p>
            </section>

            <div className="safety-notice">
                <div className="notice-icon">
                    <Icon name="warning" size={17} />
                </div>

                <div>
                    <strong>Emergency Notice</strong>

                    <p>
                        MeshAid is a supplemental disaster communication system.
                        Message delivery is not guaranteed and this service does
                        not replace 911 or official emergency services.
                    </p>
                </div>
            </div>

            <div
                className={
                    backendOnline
                        ? meshOnline
                            ? "connection-banner"
                            : "connection-banner connection-warning"
                        : "connection-banner connection-offline"
                }
            >
                <div>
                    <span className="connection-dot"></span>

                    <div>
                        <strong>
                            {!backendOnline
                                ? "Help Point Unavailable"
                                : meshOnline
                                    ? "Mesh Network Connected"
                                    : "Mesh Network Unavailable"}
                        </strong>

                        <span>
                            {!backendOnline
                                ? "The local Help Point service cannot currently be reached."
                                : meshOnline
                                    ? "Requests can be sent through the local mesh network."
                                    : "Requests can still be accepted and queued for later delivery."}
                        </span>
                    </div>
                </div>

                <span className="connection-badge">
                    {!backendOnline
                        ? "OFFLINE"
                        : meshOnline
                            ? "ONLINE"
                            : "QUEUEING"}
                </span>
            </div>

            {backendOnline && queueDepth > 0 && (
                <div className="queue-banner">
                    <strong>
                        {queueDepth} pending{" "}
                        {queueDepth === 1 ? "message" : "messages"}
                    </strong>

                    <span>
                        Stored locally and waiting for mesh connectivity.
                    </span>
                </div>
            )}

            <section className="services">

                <div className="section-heading">
                    <h2>Available Services</h2>
                    <span>Select a service</span>
                </div>

                <div className="service-grid">

                    <Link
                        to="/check-in"
                        className="service-card checkin-card"
                    >
                        <div className="service-icon">
                            <Icon name="check" size={23} />
                        </div>

                        <div>
                            <h3>Safety Check-In</h3>

                            <p>
                                Let emergency coordinators know you are safe.
                            </p>
                        </div>

                        <span className="card-arrow">→</span>
                    </Link>

                    <Link
                        to="/medical"
                        className="service-card medical-card"
                    >
                        <div className="service-icon">
                            <Icon name="medical" size={25} />
                        </div>

                        <div>
                            <h3>Medical Assistance</h3>

                            <p>
                                Report an urgent medical need.
                            </p>
                        </div>

                        <span className="card-arrow">→</span>
                    </Link>

                    <Link
                        to="/resources"
                        className="service-card resource-card"
                    >
                        <div className="service-icon">
                            <Icon name="resources" size={23} />
                        </div>

                        <div>
                            <h3>Request Resources</h3>

                            <p>
                                Request food, water, medicine, or shelter.
                            </p>
                        </div>

                        <span className="card-arrow">→</span>
                    </Link>

                </div>
            </section>

            <section className="updates-section">

                <div className="section-heading">
                    <h2>Emergency Information</h2>
                </div>

                <Link
                    to="/messages"
                    className="messages-card"
                >
                    <div className="message-symbol">
                        <Icon name="messages" size={20} />
                    </div>

                    <div className="message-preview">
                        <h3>Messages & Announcements</h3>

                        <p>
                            View emergency warnings and local relief information.
                        </p>
                    </div>

                    <span className="card-arrow">→</span>
                </Link>

            </section>

            <p className="terminal-note">
                Local emergency network • Internet connection not required
            </p>

        </div>
    );
}

export default Home;