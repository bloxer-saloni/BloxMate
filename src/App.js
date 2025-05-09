import React from "react";
import { BrowserRouter as Router, Routes, Route } from "react-router-dom";
import ChatBot from "./components/ChatBot";
import LearningsDashboard from "./components/LearningsDashboard";
import HomePage from "./components/HomePage"; // Import HomePage

export default function App() {
  return (
    <Router>
      <Routes>
        {/* Route for HomePage */}
        <Route path="/home" element={<HomePage />} />

        {/* Route for ChatBot */}
        <Route path="/" element={<ChatBot />} />

        {/* Route for LearningsDashboard */}
        <Route path="/learnings-dashboard" element={<LearningsDashboard />} />
      </Routes>
    </Router>
  );
}
