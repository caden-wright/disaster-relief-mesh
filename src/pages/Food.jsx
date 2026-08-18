import { useState } from "react";
import { Link } from "react-router-dom";

function Food(){

    const [hungry, setHungry] = useState("");
    const [sustenance, setSustenance] = useState("Both");
    const [urgency, setUrgency] = useState("Low");
    const [location, setLocation] = useState("");
    const [description, setDescription] = useState("");

    function handleSubmit(){

        if (Number(hungry) <= 0) {
            alert("Please enter a valid number of people.");
            return;
        }

        if (location.trim() === "") {
            alert("Please enter an approximate location.");
            return;
        }

        const request = {
            hungry,
            sustenance,
            urgency,
            location,
            description
        };

        console.log("Food Request:", request);
        alert('Food & Water Request Sent');

        setHungry("");
        setSustenance("Both");
        setUrgency("Low");
        setLocation("");
        setDescription("");
    }

    return (
        <div>
            <h1>Disaster Relief Network</h1>
            <h3>Food & Water</h3>
            <p>
                Please describe your food and water needs below.
            </p>

            <label
            htmlFor="hungry">
                How many people need assistance?
            </label>

            <input 
            type="number"
            value={hungry}
            onChange={(event) => setHungry(event.target.value)}
            />

            <label>What sustenance is needed?</label>

            <select
                value={sustenance}
                onChange={(event) => setSustenance(event.target.value)}>
                <option value="Food">Food</option>
                <option value="Water">Water</option>
                <option value="Both">Both</option>
            </select>

            <label>Urgency</label>
            <select
                value={urgency}
                onChange={(event) => setUrgency(event.target.value)}>
                <option value="Low">Low</option>
                <option value="Medium">Medium</option>
                <option value="High">High</option>
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

            <button onClick={handleSubmit}>
                Submit
            </button>

            <Link to="/"> 
                <button>Back to Home</button>
            </Link>

        </div>
    );
}

export default Food;