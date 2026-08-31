import { Link } from "react-router-dom";
import "./Home.css";
import Icon from "../components/Icon";

function Home() {
    return (
        <div className="home-container">

            <section className="home-intro">
                <span className="eyebrow">HELP POINT TERMINAL</span>

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

            <div className="connection-banner">
                <div>
                    <span className="connection-dot"></span>

                    <div>
                        <strong>Connected to Help Point</strong>
                        <span>
                            Requests can be submitted through this local station.
                        </span>
                    </div>
                </div>

                <span className="connection-badge">ONLINE</span>
            </div>

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

                <Link to="/messages" className="messages-card">

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