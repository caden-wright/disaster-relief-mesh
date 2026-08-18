import { Link } from "react-router-dom";
import { useState } from "react";

function Shelter() {

    const [people, setPeople] = useState("");
    const [children, setChildren] = useState("No");
    const [pets, setPets] = useState("No");
    const [accessibility, setAccessibility] = useState("No");
    const [location, setLocation] = useState("");
    const [description, setDescription] = useState("");

    function handleSubmit() {

        if (Number(people) <= 0) {
            alert("Please enter the number of people.");
            return;
        }

        if (location.trim() === "") {
            alert("Please enter an approximate location.");
            return;
        }

        const request = {
            people,
            children,
            pets,
            accessibility,
            location,
            description
        };

        console.log("Shelter Request:", request);

        alert("Shelter request submitted successfully!");

        setPeople("");
        setChildren("No");
        setPets("No");
        setAccessibility("No");
        setLocation("");
        setDescription("");
    }

    return (
        <div>
            <h1>Disaster Relief Network</h1>

            <h3>Shelter Request</h3>

            <p>Please describe your shelter needs.</p>

            <label>Number of People</label>
            <input
                type="number"
                value={people}
                onChange={(e) => setPeople(e.target.value)}
            />

            <label>Children Present?</label>
            <select
                value={children}
                onChange={(e) => setChildren(e.target.value)}
            >
                <option>Yes</option>
                <option>No</option>
            </select>

            <label>Pets Present?</label>
            <select
                value={pets}
                onChange={(e) => setPets(e.target.value)}
            >
                <option>Yes</option>
                <option>No</option>
            </select>

            <label>Accessibility Needs?</label>
            <select
                value={accessibility}
                onChange={(e) => setAccessibility(e.target.value)}
            >
                <option>No</option>
                <option>Wheelchair</option>
                <option>Medical Equipment</option>
                <option>Other</option>
            </select>

            <label>Approximate Location</label>
            <input
                type="text"
                value={location}
                onChange={(e) => setLocation(e.target.value)}
                placeholder="Example: Community Center"
            />

            <label>Additional Information</label>

            <textarea
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                placeholder="Describe your shelter needs..."
            />

            <button
                onClick={handleSubmit}
                disabled={people === "" || location === ""}
            >
                Submit
            </button>

            <Link to="/">
                <button>Back to Home</button>
            </Link>

        </div>
    );
}

export default Shelter;