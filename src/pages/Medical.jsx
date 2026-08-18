import { Link } from "react-router-dom";
import { useState } from "react";

function Medical(){

    const [injured, setInjured] = useState("")
    const [severity, setSeverity] = useState("Minor")
    const [conscious, setConscious] = useState("Unknown");
    const [breathing, setBreathing] = useState("Unknown");
    const [location, setLocation] = useState("");
    const [description, setDescription] = useState("");

    function handleSubmit() {

        if (Number(injured) <= 0) {
            alert("Please enter a valid number of injured people.");
            return;
        }

        if (location.trim() === "") {
            alert("Please enter an approximate location.");
            return;
        }

        const request = {
            injured,
            severity,
            conscious,
            breathing,
            location,
            description
        };

        console.log("Medical Request:", request);

        alert("Medical request submitted successfully!");

        // Reset the form
        setInjured("");
        setSeverity("Minor");
        setConscious("Unknown");
        setBreathing("Unknown");
        setLocation("");
        setDescription("");
}

    return (
        <div>
            <h1>Disaster Relief Network</h1>

            <h3>Medical Assistance</h3>

            <p>
                Describe your medical emergency below.
            </p>

            <label htmlFor="injured">
                How many injured?
                </label>

            <input 
                type="number"
                value={injured}
                onChange={(event) => setInjured(event.target.value)}
            />

            <label>
                Severity
            </label>

            <select
                value={severity}
                onChange={(event) => setSeverity(event.target.value)}
            >

                <option>Minor</option>
                <option>Serious</option>
                <option>Critical</option>
            </select>


            <label>Are the injured conscious?</label>
            <select
                value={conscious}
                onChange={(event) => setConscious(event.target.value)}
            >
                <option>Yes</option>
                <option>No</option>
                <option>Unknown</option>
            </select>

            <label>Are they breathing?</label>
            <select
                value={breathing}
                onChange={(event) => setBreathing(event.target.value)}
            >
                <option>Yes</option>
                <option>No</option>
                <option>Unknown</option>
            </select>

            <label>Approximate Location</label>
            <input
                type="text"
                value={location}
                onChange={(event) => setLocation(event.target.value)}
                placeholder="Example: Apartment 204, second floor"
            />


            <label>Additional Information</label>

            <textarea
            value={description}
            onChange={(event) => setDescription(event.target.value)}
            placeholder="Describe the emergency..."
            />

            <button
                onClick={handleSubmit}
                disabled={injured === "" || location === ""}
            >
                Submit
            </button>

            <Link to="/">
                <button>Back to Home</button>
            </Link>

        </div>
    );
}

export default Medical;