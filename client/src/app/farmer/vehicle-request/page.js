"use client";

import React, { useEffect, useRef, useState } from "react";
import { Mic, Leaf, Home, Package, X } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";

const promptsData = [
  {
    id: "crop",
    text: "फ़सल का नाम",
    icon: Leaf,
    color: "bg-[var(--chart-1)]",
  },
  {
    id: "market",
    text: "मंडी का नाम",
    icon: Home,
    color: "bg-[var(--chart-4)]",
  },
  {
    id: "quantity",
    text: "मात्रा किलो या बोरी में",
    icon: Package,
    color: "bg-[var(--chart-2)]",
  },
];

export default function VoiceForm() {
  const [showTooltip, setShowTooltip] = useState(true);
  const [currentStep, setCurrentStep] = useState(0);
  const [responses, setResponses] = useState({
    crop: "",
    market: "",
    quantity: "",
  });
  const [listening, setListening] = useState(false);
  const [statusText, setStatusText] = useState("");
  const [submitEnabled, setSubmitEnabled] = useState(false);

  const recognitionRef = useRef(null);
  const synthRef = useRef(null);
  const voicesRef = useRef([]);
  const stepIndexRef = useRef(0);

  const SpeechRecognition =
    typeof window !== "undefined"
      ? window.SpeechRecognition || window.webkitSpeechRecognition
      : null;
  const SpeechSynthesisUtterance =
    typeof window !== "undefined"
      ? window.SpeechSynthesisUtterance || window.webkitSpeechSynthesisUtterance
      : null;

  useEffect(() => {
    if (!SpeechRecognition) {
      alert(
        "आपका ब्राउज़र स्पीच रिकग्निशन को सपोर्ट नहीं करता है। कृपया Chrome, Edge या Safari का उपयोग करें।"
      );
      return;
    }

    synthRef.current = window.speechSynthesis;

    const loadVoices = () => {
      const voices = synthRef.current.getVoices();
      if (voices.length > 0) {
        voicesRef.current = voices;
      }
    };

    loadVoices();
    if (typeof window !== "undefined") {
      window.speechSynthesis.onvoiceschanged = loadVoices;
    }

    const recognition = new SpeechRecognition();
    recognition.lang = "hi-IN";
    recognition.continuous = false;
    recognition.interimResults = false;

    recognition.onresult = (event) => {
      const speechResult = event.results[0][0].transcript;
      const stepKey = recognition.stepKey;

      setResponses((prev) => ({
        ...prev,
        [stepKey]: speechResult,
      }));

      stopListening();
      moveToNextStep();
    };

    recognition.onerror = (event) => {
      console.error("Speech recognition error:", event.error);
      setStatusText(`त्रुटि: ${event.error}`);
      setListening(false);
      setTimeout(() => {
        startListening(promptsData[stepIndexRef.current].id);
      }, 1000);
    };

    recognition.onend = () => {
      setListening(false);
    };

    recognitionRef.current = recognition;

    setTimeout(() => {
      initApp();
    }, 1000);
  }, []);

  async function speak(text) {
    if (!SpeechSynthesisUtterance || !synthRef.current) return;

    return new Promise((resolve) => {
      let hindiVoice = voicesRef.current.find(
        (voice) =>
          voice.lang.toLowerCase().includes("hi") ||
          voice.name.toLowerCase().includes("hindi")
      );

      if (!hindiVoice && voicesRef.current.length > 0) {
        hindiVoice = voicesRef.current[0];
      }

      const utterance = new SpeechSynthesisUtterance(text);
      utterance.voice = hindiVoice;
      utterance.rate = 0.9;
      utterance.pitch = 1;
      utterance.volume = 1;
      utterance.onend = resolve;

      synthRef.current.cancel();
      synthRef.current.speak(utterance);
    });
  }

  function startListening(stepKey) {
    const recognition = recognitionRef.current;
    if (!recognition || listening) return;

    try {
      recognition.stepKey = stepKey;
      recognition.start();
      setListening(true);
      setStatusText("सुन रहा है...");
    } catch (error) {
      console.warn("Speech recognition start error:", error);
    }
  }

  function stopListening() {
    const recognition = recognitionRef.current;
    if (!recognition) return;

    try {
      recognition.stop();
      setListening(false);
      setStatusText("");
    } catch (error) {
      console.error("Recognition stop error:", error);
    }
  }

  async function moveToNextStep() {
    if (stepIndexRef.current < promptsData.length - 1) {
      stepIndexRef.current += 1;
      const nextPrompt = promptsData[stepIndexRef.current];
      setCurrentStep(stepIndexRef.current);
      await speak(nextPrompt.text);
      startListening(nextPrompt.id);
    } else {
      setSubmitEnabled(true);
      setStatusText("सभी चरण पूर्ण हो गए हैं। आप भेज सकते हैं।");
    }
  }

  async function initApp() {
    stepIndexRef.current = 0;
    setCurrentStep(0);
    setResponses({ crop: "", market: "", quantity: "" });
    setSubmitEnabled(false);
    setStatusText("");
    await speak(
      "कृपया अपनी फसल, मंडी और मात्रा बताएं। अब बताएं " + promptsData[0].text
    );
    startListening(promptsData[0].id);
  }

  async function onMicClick() {
    if (synthRef.current.speaking) synthRef.current.cancel();
    await speak(promptsData[stepIndexRef.current].text);
    startListening(promptsData[stepIndexRef.current].id);
  }

  async function onSubmit() {
    if (!navigator.geolocation) {
      alert("लोकेशन प्राप्त नहीं हो सकी। कृपया लोकेशन एक्सेस की अनुमति दें।");
      return;
    }

    navigator.geolocation.getCurrentPosition(
      async (position) => {
        const { latitude, longitude } = position.coords;

        const res = await fetch("/api/voice-response", {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            ...responses,
            latitude,
            longitude,
          }),
        });

        if (res.ok) {
          alert(
            `आपका अनुरोध भेजा गया है:\nफसल: ${responses.crop}\nमंडी: ${responses.market}\nमात्रा: ${responses.quantity}`
          );
          await speak("आपका ट्रक आने वाला है, कृपया कुछ समय प्रतीक्षा करें।");
          window.location.href = "http://127.0.0.1:5000/";
        } else {
          alert("डेटा सेव करने में त्रुटि हुई। कृपया पुनः प्रयास करें।");
        }
      },
      (error) => {
        console.error("Geolocation error:", error);
        alert("लोकेशन प्राप्त करने में त्रुटि हुई।");
      }
    );
  }

  return (
    <div className="max-w-2xl mx-auto mt-20 p-4">
      <div className="flex flex-col items-center mb-6 relative">
        {showTooltip && (
          <div className="absolute -top-14 bg-white text-sm text-gray-800 px-4 py-2 rounded shadow-md flex items-center space-x-2">
            <span>हर उत्तर देने के लिए माइक को दबाएँ</span>
            <button
              onClick={() => setShowTooltip(false)}
              className="text-gray-500 hover:text-gray-700"
            >
              <X className="w-4 h-4 cursor-pointer" />
            </button>
          </div>
        )}

        <div
          className={`p-4 bg-gray-200 rounded-full cursor-pointer border-4 transition ${
            listening ? "border-indigo-600 animate-pulse" : "border-transparent"
          }`}
          onClick={onMicClick}
        >
          <Mic className="text-indigo-600 w-6 h-6" />
        </div>
      </div>

      <h1 className="text-2xl font-bold text-center mb-6">बोलिए</h1>

      <div className="space-y-6">
        {promptsData.map((prompt, index) => (
          <Card
            key={prompt.id}
            className={`p-4 rounded-xl min-h-[100px] shadow ${
              index === currentStep ? "ring-2 ring-indigo-600" : ""
            }`}
          >
            <div className="flex items-center space-x-4">
              <prompt.icon className="w-6 h-6" />
              <span className="font-semibold">{prompt.text}</span>
            </div>
            <div className="mt-2 text-lg font-medium">
              {responses[prompt.id] && `आपका उत्तर: ${responses[prompt.id]}`}
            </div>
          </Card>
        ))}
      </div>

      <div className="flex items-center justify-center">
        <Button
          onClick={onSubmit}
          disabled={!submitEnabled}
          className={`mt-6 max-w-sm py-2 px-4 rounded-xl font-semibold transition cursor-pointer ${
            submitEnabled
              ? "bg-indigo-600 hover:bg-indigo-700 text-white"
              : "bg-gray-400"
          }`}
        >
          भेजिए ट्रक
        </Button>
      </div>

      {statusText && (
        <div className="mt-4 text-center text-xl text-gray-700">
          {statusText}
        </div>
      )}
    </div>
  );
}