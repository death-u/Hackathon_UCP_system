function showSection(id){
    const sections = document.querySelectorAll('.section');
    const target = document.getElementById(id);

    sections.forEach(sec => {
        if(sec.classList.contains('active')){
            gsap.to(sec, {opacity: 0, y: -20, duration: 0.3, onComplete: () => {
                sec.classList.remove('active');
                target.classList.add('active');
                gsap.fromTo(target, 
                    { opacity: 0, y: 20 }, 
                    { opacity: 1, y: 0, duration: 0.4 }
                );
            }});
        }
    });
}

gsap.from(".card", {
    opacity: 0,
    y: 40,
    duration: 0.8,
    stagger: 0.1,
    ease: "power2.out"
});

function showSection(id){
        const sections = document.querySelectorAll('.section');
        const target = document.getElementById(id);
        sections.forEach(sec => {
            if(sec.classList.contains('active')){
                gsap.to(sec, {opacity: 0, y: -20, duration: 0.3, onComplete: () => {
                    sec.classList.remove('active');
                    target.classList.add('active');
                    gsap.fromTo(target, { opacity: 0, y: 20 }, { opacity: 1, y: 0, duration: 0.4 });
                }});
            }
        });
    }