// Import the functions you need from the SDKs you need
import { initializeApp } from "https://www.gstatic.com/firebasejs/10.7.1/firebase-app.js";
import { getFirestore } from "https://www.gstatic.com/firebasejs/10.7.1/firebase-firestore.js";
// TODO: Add SDKs for Firebase products that you want to use
// https://firebase.google.com/docs/web/setup#available-libraries

// Your web app's Firebase configuration
const firebaseConfig = {
  apiKey: "AIzaSyA_QEnNbDueGVx3_lUuKJjppibuLF9wTmg",
  authDomain: "agripulse-3bfce.firebaseapp.com",
  projectId: "agripulse-3bfce",
  storageBucket: "agripulse-3bfce.firebasestorage.app",
  messagingSenderId: "120911407524",
  appId: "1:120911407524:web:265338a7791b3bbb8a3931"
};

// Initialize Firebase
const app = initializeApp(firebaseConfig);
export const db = getFirestore(app);