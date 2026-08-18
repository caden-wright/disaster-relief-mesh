import { Link } from "react-router-dom";

function Messages(){

    const messages = [
        {
            id: 1,
            title: "Medical Team Dispatched",
            body: "Medical responders are on the way to your location.",
            time: "5 minutes ago"
        },
        {
            id: 2,
            title: "Flood Warning",
            body: "Avoid low-lying roads near the river.",
            time: "18 minutes ago"
        },
        {
            id: 3,
            title: "Food Distribution",
            body: "Meals and bottled water are available at the Community Center.",
            time: "35 minutes ago"
        }
    ];

    return (
        <div>

            <h1>Disaster Relief Network</h1>

            <h2>Messages</h2>

            <p>
                Emergency updates from responders.
            </p>

            {messages.map((message) => (

                <div key={message.id}>

                    <h4>{message.title}</h4>

                    <p>{message.body}</p>

                    <small>{message.time}</small>

                    <hr />

                </div>

            ))}
        
            <Link to="/">
                <button>Back to Home</button>
            </Link>

        </div>
    );
}

export default Messages;