import React, { useState } from "react";
import SetupPage from "./pages/SetupPage";
import GamePage from "./pages/GamePage";

export default function App() {
  const [started, setStarted] = useState(false);

  return started ? (
    <GamePage />
  ) : (
    <SetupPage onStart={() => setStarted(true)} />
  );
}
