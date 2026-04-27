// ================= Utility =================
function show(el) {
  el.classList.remove('d-none');
}

function hide(el) {
  el.classList.add('d-none');
}

// ================= FORM SUBMISSION =================
document.getElementById('uploadForm').addEventListener('submit', async function (e) {
  e.preventDefault();

  const spinner = document.getElementById('loadingSpinner');
  const results = document.getElementById('results');
  const skillsSection = document.getElementById('skillsSection');
  const summary = document.getElementById('summary');
  const atsScoreEl = document.getElementById('atsScore');
  const skillList = document.getElementById('missingSkills');
  const improvementList = document.getElementById('improvements');
  const resumeSkillsEl = document.getElementById('resumeSkills');
  const jdSkillsEl = document.getElementById('jdSkills');

  show(spinner);
  hide(results);

  const formData = new FormData(this);

  try {
    const response = await fetch('/analyze', {
      method: 'POST',
      body: formData
    });

    const data = await response.json();

    hide(spinner);
    show(results);

    // ================= ATS SCORE =================
    const score = Number(data.final_ats_score || 0);

    atsScoreEl.textContent = score + "%";
    atsScoreEl.style.color =
      score >= 80 ? 'green' :
      score >= 50 ? 'orange' :
      'red';

    // ================= SUMMARY =================
    summary.innerText = data.summary || "No summary generated.";

    // ================= MISSING SKILLS =================
    skillList.innerHTML = '';
    (data.missing_skills || []).forEach(skill => {
      const li = document.createElement('li');
      li.className = 'list-group-item';
      li.innerText = skill;
      skillList.appendChild(li);
    });

    // ================= IMPROVEMENTS =================
    improvementList.innerHTML = '';
    (data.improvements || []).forEach(tip => {
      const li = document.createElement('li');
      li.className = 'list-group-item';
      li.innerText = tip;
      improvementList.appendChild(li);
    });

    // ================= SKILLS MATCH SECTION =================
    resumeSkillsEl.innerHTML = '';
    jdSkillsEl.innerHTML = '';

    const resumeSkills = data.resume_skills || [];
    const analysis = data.analysis || [];

    if (resumeSkills.length || analysis.length) {

      // Resume Skills (always green)
      resumeSkills.forEach(skill => {
        const li = document.createElement('li');
        li.className = 'list-group-item text-success';
        li.innerHTML = `✅ ${skill}`;
        resumeSkillsEl.appendChild(li);
      });

      // JD Skills (based on backend semantic result)
      analysis.forEach(item => {
        const li = document.createElement('li');
        li.classList.add('list-group-item');

        if (item.status === "Full Match") {
          li.innerHTML = `✅ ${item.jd_skill}`;
          li.classList.add('text-success');
        } 
        else if (item.status === "Partial Match") {
          li.innerHTML = `⚠️ ${item.jd_skill}`;
          li.classList.add('text-warning');
        } 
        else {
          li.innerHTML = `❌ ${item.jd_skill}`;
          li.classList.add('text-danger');
        }

        jdSkillsEl.appendChild(li);
      });

      show(skillsSection);

    } else {
      hide(skillsSection);
    }

  } catch (error) {
    hide(spinner);
    alert('Something went wrong. Please try again.');
    console.error('Error during analysis:', error);
  }
});

// ================= CHAT BOX =================
async function sendMessage() {
  const input = document.getElementById('chatInput');
  const sendBtn = document.getElementById('sendBtn');
  const loading = document.getElementById('chatLoading');
  const chatBox = document.getElementById('chatBox');

  const message = input.value.trim();
  if (!message) return;

  const userMsg = document.createElement('div');
  userMsg.innerHTML = `<strong>You:</strong> ${message}`;
  chatBox.appendChild(userMsg);

  input.disabled = true;
  sendBtn.disabled = true;
  show(loading);
  input.value = '';

  try {
    const response = await fetch('/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message })
    });

    const data = await response.json();
    let text = data.response || "No response.";

    const formatted = text.replace(/\n/g, '<br>');

    const aiMsg = document.createElement('div');
    aiMsg.innerHTML = `<strong>Gemini:</strong><br>${formatted}`;
    chatBox.appendChild(aiMsg);

  } catch (err) {
    const errMsg = document.createElement('div');
    errMsg.classList.add('text-danger');
    errMsg.innerText = 'Error: Could not get a response.';
    chatBox.appendChild(errMsg);
  } 
  finally {
    input.disabled = false;
    sendBtn.disabled = false;
    hide(loading);
    chatBox.scrollTop = chatBox.scrollHeight;
  }
}
