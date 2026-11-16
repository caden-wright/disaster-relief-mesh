import { Link } from "react-router-dom";
import "./Messages.css";

function Messages() {

    // DI-09: Help Points only send uplink today; there is no channel for
    // Incident Command to push alerts down to them yet. Show an honest empty
    // state instead of sample alerts until two-way messaging exists.
    const messages = [];

    return (
        <div className="messages-page">

            <header className="messages-header">
                <h1>Messages & Alerts</h1>

                <p>
                    View emergency warnings, responder updates, and
                    relief information received through the mesh network.
                </p>
            </header>

            <div className="messages-summary">
                <h2>Recent Messages</h2>

                <span className="messages-count">
                    {messages.length} messages
                </span>
            </div>

            <div className="message-list">

                {messages.length === 0 && (
                    <p className="messages-empty">
                        No alerts have been received at this Help Point.
                        Check back with staff here for the latest updates.
                    </p>
                )}

                {messages.map((message) => (

                    <article
                        key={message.id}
                        className={`message-card ${message.style}`}
                    >

                        <div className="message-meta">

                            <span className="message-type">
                                {message.type}
                            </span>

                            <span className="message-time">
                                {message.time}
                            </span>

                        </div>

                        <h3>{message.title}</h3>

                        <p>{message.body}</p>

                    </article>

                ))}

            </div>

            <div className="messages-actions">
                <Link to="/">
                    <button className="messages-back-button">
                        Back to Home
                    </button>
                </Link>
            </div>

        </div>
    );
}

export default Messages;