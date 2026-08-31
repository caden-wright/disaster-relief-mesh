import { Link } from "react-router-dom";
import "./Messages.css";

function Messages() {

    const messages = [
    {
        id: 1,
        type: "Emergency Alert",
        style: "warning",
        title: "Flood Warning",
        body: "Avoid low-lying roads near the river.",
        time: "5 minutes ago"
    },
    {
        id: 2,
        type: "Relief Update",
        style: "relief",
        title: "Food Distribution Available",
        body: "Meals and bottled water are available at the Community Center.",
        time: "18 minutes ago"
    },
    {
        id: 3,
        type: "Shelter Update",
        style: "relief",
        title: "Shelter Capacity Available",
        body: "Temporary shelter space is available at the North Help Point.",
        time: "35 minutes ago"
    }
    ];

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