import { Link } from "react-router-dom";
import { useState } from "react";

function Hazard() {

    const [hazardType, setHazardType] = useState("Flood");
    const [severity, setSeverity] = useState("Low");
    const [location, setLocation] = useState("");
    const [description, setDescription] = useState("");

    function handleSubmit() {

        if (location.trim() === "") {
            alert("Please enter an approximate location.");
            return;
        }

        const request = {
            hazardType,
            severity,
            location,
            description
        };

        console.log("Hazard Report:", request);

        alert("Hazard report submitted successfully!");

        // Reset form
        setHazardType("Flood");
        setSeverity("Low");
        setLocation("");
        setDescription("");
    }

    return (
        <div>
            <h1>Disaster Relief Network</h1>

            <h3>Hazard Report</h3>

            <p>
                Report a hazard so responders can warn others and prioritize assistance.
            </p>

            <label>Hazard Type</label>

            <select
                value={hazardType}
                onChange={(e) => setHazardType(e.target.value)}
            >
                <option>Flood</option>
                <option>Fire</option>
                <option>Gas Leak</option>
                <option>Road Blocked</option>
                <option>Power Outage</option>
                <option>Other</option>
            </select>

            <label>Severity</label>

            <select
                value={severity}
                onChange={(e) => setSeverity(e.target.value)}
            >
                <option>Low</option>
                <option>Medium</option>
                <option>High</option>
            </select>

            <label>Approximate Location</label>

            <input
                type="text"
                value={location}
                onChange={(e) => setLocation(e.target.value)}
                placeholder="Example: Main Street near City Hall"
            />

            <label>Additional Information</label>

            <textarea
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                placeholder="Describe the hazard..."
            />

            <button
                onClick={handleSubmit}
                disabled={location === ""}
            >
                Submit
            </button>

            <Link to="/">
                <button>Back to Home</button>
            </Link>

        </div>
    );
}

export default Hazard;