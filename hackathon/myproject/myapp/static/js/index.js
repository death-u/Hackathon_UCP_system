
    const loginPassword = document.getElementById("loginPassword");
    const l_email = document.getElementById("l_email")

    loginPassword.textContent = ""
    l_email.textContent = ""


// Toggle password visibility
function togglePassword(id){
    const input = document.getElementById(id);
    input.type = input.type === "password" ? "text" : "password";
    let toggle_password = document.querySelector(".toggle-password")
    if(input.type === "text"){
        toggle_password.textContent = "Hide"
    }
    else {       
        toggle_password.textContent = "show"
    }
}

// Switch between login and register
function switchForm(){
    const login = document.getElementById("loginForm");
    const register = document.getElementById("registerForm");

    if(login.style.display !== "none"){
        gsap.to(login, {opacity:0, y:-20, duration:0.3, onComplete:()=>{
            login.style.display="none";
            register.style.display="flex";
            gsap.fromTo(register,{opacity:0,y:20},{opacity:1,y:0,duration:0.4});
        }});
    } else {
        gsap.to(register, {opacity:0, y:-20, duration:0.3, onComplete:()=>{
            register.style.display="none";
            login.style.display="flex";
            gsap.fromTo(login,{opacity:0,y:20},{opacity:1,y:0,duration:0.4});
        }});
    }
}

// Page entrance animation
gsap.from(".auth-container",{
    opacity:0,
    y:40,
    duration:1,
    ease:"power3.out"
});
