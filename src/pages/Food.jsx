import "./Form.css";
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
        <div className="page-container">

            <header className="page-header">
                <h1 className="page-title">Food & Water Assistance</h1>

                <p className="page-description">
                    Request emergency food, drinking water, or both for
                    yourself or others at your location.
                </p>
            </header>

            <div className="form-card">

                <div className="form-group">
                    <label htmlFor="hungry">
                        How many people need assistance?
                    </label>

                    <input
                        id="hungry"
                        type="number"
                        min="1"
                        value={hungry}
                        onChange={(event) => setHungry(event.target.value)}
                        placeholder="Number of people"
                    />
                </div>

                <div className="form-group">
                    <label htmlFor="sustenance">
                        What is needed?
                    </label>

                    <select
                        id="sustenance"
                        value={sustenance}
                        onChange={(event) => setSustenance(event.target.value)}
                    >
                        <option value="Food">Food</option>
                        <option value="Water">Water</option>
                        <option value="Both">Food & Water</option>
                    </select>
                </div>

                <div className="form-group">
                    <label htmlFor="urgency">
                        Urgency
                    </label>

                    <select
                        id="urgency"
                        value={urgency}
                        onChange={(event) => setUrgency(event.target.value)}
                    >
                        <option value="Low">Low</option>
                        <option value="Medium">Medium</option>
                        <option value="High">High</option>
                    </select>
                </div>

                <div className="form-group">
                    <label htmlFor="location">
                        Approximate Location
                    </label>

                    <input
                        id="location"
                        type="text"
                        value={location}
                        onChange={(event) => setLocation(event.target.value)}
                        placeholder="Example: Apartment 204, second floor"
                    />
                </div>

                <div className="form-group">
                    <label htmlFor="description">
                        Additional Information
                    </label>

                    <textarea
                        id="description"
                        value={description}
                        onChange={(event) => setDescription(event.target.value)}
                        placeholder="Describe quantities needed or other important information..."
                    />
                </div>

                <div className="form-actions">

                    <button
                        className="submit-button"
                        onClick={handleSubmit}
                        disabled={hungry === "" || location.trim() === ""}
                    >
                        Submit Food & Water Request
                    </button>

                    <Link to="/" style={{ flex: 1 }}>
                        <button className="back-button">
                            Back to Home
                        </button>
                    </Link>

                </div>

            </div>
        </div>
    );
}

export default Food;