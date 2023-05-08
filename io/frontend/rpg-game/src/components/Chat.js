import React, { useState, useEffect, useRef } from "react";
import { io } from "socket.io-client";
import "./Chat.css";

const API_ROOT = process.env.REACT_APP_API_ROOT;


const Chat = () => {
  const [messages, setMessages] = useState([]);
  const messagesEndRef = useRef(null);

  useEffect(() => {
    const socket = io(API_ROOT);

    socket.on("connect", () => {
      console.log("Connected to the server");
    });

    socket.on("welcome", (event) => {
      console.log(event.message);
    });

    socket.on("server_message", (event) => {
      console.log("Received message:", event);

      const data = event.message;
      const newMessages = data.map((messageData) => {
        const [sender, text] = messageData.split("|");
        const colors = ["red", "green", "blue", "orange", "purple"];
        const randomIndex = Math.floor(Math.random() * colors.length);
        const randomColor = colors[randomIndex];

        return {
          sender,
          text,
          time: new Date(),
          color: randomColor,
        };
      });

      setMessages((prevMessages) => [...prevMessages, ...newMessages]);
    });

    socket.on("disconnect", () => {
      console.log("Disconnected from the server");
    });

    return () => {
      socket.disconnect();
    };
  }, []);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  return (
    <div>
        <div className="chat-container">
        <div className="messages-container">
            {messages.map((message, index) => (
            <div key={index} className="message">
                <span style={{ fontWeight: "bold", color: message.color }}>
                {message.sender}
                </span>
                : {message.text}
            </div>
            ))}
            <div ref={messagesEndRef}></div>
        </div>
        </div>

    </div>
  );
};

export default Chat;
