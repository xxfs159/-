const $ = (selector) => document.querySelector(selector);

const dom = {
  pet: $("#pet"),
  petThought: $("#petThought"),
  presenceChip: $("#presenceChip"),
  moodChip: $("#moodChip"),
  cameraButton: $("#cameraButton"),
  micButton: $("#micButton"),
  voiceButton: $("#voiceButton"),
  snapshotButton: $("#snapshotButton"),
  video: $("#cameraVideo"),
  canvas: $("#analysisCanvas"),
  placeholder: $("#cameraPlaceholder"),
  brightnessValue: $("#brightnessValue"),
  motionValue: $("#motionValue"),
  faceValue: $("#faceValue"),
  agentState: $("#agentState"),
  inputCount: $("#inputCount"),
  lastAction: $("#lastAction"),
  chatLog: $("#chatLog"),
  chatForm: $("#chatForm"),
  chatInput: $("#chatInput"),
  apiBase: $("#apiBase"),
  modelName: $("#modelName"),
  apiKey: $("#apiKey"),
  saveModelButton: $("#saveModelButton"),
};

const state = {
  cameraActive: false,
  voiceEnabled: true,
  stream: null,
  scanTimer: null,
  faceDetector: null,
  lastFrame: null,
  brightness: null,
  motion: null,
  faceCount: null,
  inputEvents: 0,
  lastInputAt: Date.now(),
  lastAction: "等待",
  mood: "idle",
  snapshot: null,
  messages: [],
  model: {
    apiBase: "",
    modelName: "",
    apiKey: "",
  },
};

const moodText = {
  idle: "待机",
  typing: "同步输入",
  curious: "好奇观察",
  cheer: "鼓励中",
  sleepy: "休息",
  thinking: "思考",
};

function init() {
  loadModelConfig();
  bindEvents();
  addMessage("pet", "你好，我是项目39的具身桌宠原型。你可以开启摄像头，让我根据亮度、动作和人脸状态改变反应，也可以直接和我聊天。");
  setMood("idle", "我在等你唤醒摄像头或和我聊天。");
  updatePanel();
  window.setInterval(proactiveTick, 9000);
}

function bindEvents() {
  dom.cameraButton.addEventListener("click", toggleCamera);
  dom.micButton.addEventListener("click", startSpeechInput);
  dom.voiceButton.addEventListener("click", toggleVoice);
  dom.snapshotButton.addEventListener("click", takeSnapshot);
  dom.saveModelButton.addEventListener("click", saveModelConfig);
  dom.chatForm.addEventListener("submit", (event) => {
    event.preventDefault();
    sendChat(dom.chatInput.value);
  });

  document.querySelectorAll(".pad-key").forEach((button) => {
    button.addEventListener("click", () => handlePadAction(button.dataset.action));
  });

  window.addEventListener("keydown", () => registerInput("键盘输入", "typing"));
  window.addEventListener("pointerdown", () => registerInput("鼠标点击", "typing"));
}

async function toggleCamera() {
  if (state.cameraActive) {
    stopCamera();
    return;
  }

  try {
    const stream = await navigator.mediaDevices.getUserMedia({
      video: {
        facingMode: "user",
        width: { ideal: 960 },
        height: { ideal: 540 },
      },
      audio: false,
    });
    state.stream = stream;
    dom.video.srcObject = stream;
    await dom.video.play();
    state.cameraActive = true;
    dom.cameraButton.classList.add("active");
    dom.cameraButton.title = "关闭摄像头";
    document.body.classList.add("camera-on");
    if ("FaceDetector" in window) {
      state.faceDetector = new FaceDetector({ fastMode: true, maxDetectedFaces: 2 });
    }
    state.scanTimer = window.setInterval(sampleCamera, 700);
    setMood("curious", "摄像头已开启。我会在本地分析画面状态，不会上传视频。");
    addMessage("pet", "摄像头已开启。我会用本地指标判断你是否在屏幕前、环境是否偏暗、有没有明显动作。");
    speak("摄像头已开启，我开始观察。");
  } catch (error) {
    addMessage("pet", `摄像头启动失败：${error.message || "浏览器拒绝了权限"}`);
    setMood("sleepy", "没有拿到摄像头权限，我先用聊天和输入事件陪你。");
  }
  updatePanel();
}

function stopCamera() {
  state.stream?.getTracks().forEach((track) => track.stop());
  state.stream = null;
  state.cameraActive = false;
  state.lastFrame = null;
  state.faceCount = null;
  window.clearInterval(state.scanTimer);
  dom.video.srcObject = null;
  dom.cameraButton.classList.remove("active");
  dom.cameraButton.title = "开启摄像头";
  document.body.classList.remove("camera-on");
  setMood("idle", "摄像头已关闭，我还可以响应键盘、鼠标和聊天。");
  updatePanel();
}

async function sampleCamera() {
  if (!state.cameraActive || dom.video.readyState < 2) return;
  const canvas = dom.canvas;
  const context = canvas.getContext("2d", { willReadFrequently: true });
  context.drawImage(dom.video, 0, 0, canvas.width, canvas.height);

  const frame = context.getImageData(0, 0, canvas.width, canvas.height);
  const data = frame.data;
  let brightnessSum = 0;
  let diffSum = 0;
  let sampleCount = 0;

  for (let index = 0; index < data.length; index += 24) {
    const r = data[index];
    const g = data[index + 1];
    const b = data[index + 2];
    const brightness = 0.2126 * r + 0.7152 * g + 0.0722 * b;
    brightnessSum += brightness;
    if (state.lastFrame) {
      diffSum += Math.abs(brightness - state.lastFrame[index / 4]);
    }
    sampleCount += 1;
  }

  const grayFrame = new Uint8ClampedArray(data.length / 4);
  for (let index = 0, pixel = 0; index < data.length; index += 4, pixel += 1) {
    grayFrame[pixel] = Math.round(0.2126 * data[index] + 0.7152 * data[index + 1] + 0.0722 * data[index + 2]);
  }

  state.brightness = Math.round(brightnessSum / sampleCount);
  state.motion = state.lastFrame ? Math.min(100, Math.round(diffSum / sampleCount)) : 0;
  state.lastFrame = grayFrame;

  if (state.faceDetector) {
    try {
      const faces = await state.faceDetector.detect(dom.video);
      state.faceCount = faces.length;
    } catch {
      state.faceCount = null;
    }
  }

  inferMoodFromSensors();
  updatePanel();
}

function inferMoodFromSensors() {
  const idleMs = Date.now() - state.lastInputAt;
  if (state.brightness !== null && state.brightness < 54) {
    setMood("sleepy", "画面有点暗，我猜你可能在低光环境里。");
    return;
  }
  if (state.faceCount > 0) {
    setMood("curious", "我看到你在屏幕前，准备好互动了。");
    return;
  }
  if (state.motion !== null && state.motion > 18) {
    setMood("cheer", "画面里有明显动作，我保持注意。");
    return;
  }
  if (idleMs > 45000) {
    setMood("sleepy", "你安静了一会儿，我进入轻休息状态。");
    return;
  }
  setMood("idle", "环境稳定，我继续待命。");
}

function setMood(mood, thought) {
  if (state.mood !== mood) {
    dom.pet.className = `pet mood-${mood}`;
    state.mood = mood;
  }
  if (thought) {
    dom.petThought.textContent = thought;
  }
  updatePanel();
}

function handlePadAction(action) {
  const actions = {
    typing: ["模拟键盘输入", "typing", "收到键盘动作，我会像 BongoCat 一样同步敲击。"],
    mouse: ["模拟鼠标点击", "typing", "鼠标事件已记录，我会把它当作用户活跃信号。"],
    cheer: ["鼓励动作", "cheer", "保持这个节奏，今天的项目推进得很稳。"],
    sleep: ["休息动作", "sleepy", "我先趴一会儿，等你回来继续。"],
  };
  const [label, mood, thought] = actions[action] || actions.typing;
  registerInput(label, mood, thought);
}

function registerInput(label, mood = "typing", thought = "检测到输入事件，桌宠正在同步动作。") {
  state.inputEvents += 1;
  state.lastInputAt = Date.now();
  state.lastAction = label;
  setMood(mood, thought);
  updatePanel();
}

function updatePanel() {
  const presence = getPresenceLabel();
  dom.presenceChip.textContent = presence;
  dom.moodChip.textContent = moodText[state.mood] || "待机";
  dom.brightnessValue.textContent = state.brightness === null ? "--" : `${state.brightness}`;
  dom.motionValue.textContent = state.motion === null ? "--" : `${state.motion}`;
  dom.faceValue.textContent = state.faceCount === null ? "未检测" : `${state.faceCount}`;
  dom.agentState.textContent = getAgentState();
  dom.inputCount.textContent = `${state.inputEvents} 次`;
  dom.lastAction.textContent = state.lastAction;
}

function getPresenceLabel() {
  if (!state.cameraActive) return "摄像头未启用";
  if (state.faceCount > 0) return "用户在屏幕前";
  if (state.motion > 14) return "画面有动作";
  return "可能离开";
}

function getAgentState() {
  if (state.mood === "thinking") return "生成回复";
  if (state.cameraActive) return "本地感知";
  if (Date.now() - state.lastInputAt < 8000) return "输入同步";
  return "观察中";
}

function toggleVoice() {
  state.voiceEnabled = !state.voiceEnabled;
  dom.voiceButton.classList.toggle("active", state.voiceEnabled);
  dom.voiceButton.title = state.voiceEnabled ? "关闭语音播报" : "开启语音播报";
  addMessage("pet", state.voiceEnabled ? "语音播报已开启。" : "语音播报已关闭。");
}

function speak(text) {
  if (!state.voiceEnabled || !("speechSynthesis" in window)) return;
  const utterance = new SpeechSynthesisUtterance(text);
  utterance.lang = "zh-CN";
  utterance.rate = 1.02;
  utterance.pitch = 1.08;
  window.speechSynthesis.cancel();
  window.speechSynthesis.speak(utterance);
}

function startSpeechInput() {
  const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
  if (!SpeechRecognition) {
    addMessage("pet", "当前浏览器不支持语音识别，可以使用文本输入。Chrome/Edge 通常支持 Web Speech API。");
    return;
  }
  const recognition = new SpeechRecognition();
  recognition.lang = "zh-CN";
  recognition.interimResults = false;
  recognition.maxAlternatives = 1;
  dom.micButton.classList.add("active");
  setMood("curious", "我正在听你说话。");
  recognition.onresult = (event) => {
    const text = event.results[0][0].transcript;
    sendChat(text);
  };
  recognition.onerror = () => {
    addMessage("pet", "语音识别没有成功，可以再试一次或改用文本。");
  };
  recognition.onend = () => dom.micButton.classList.remove("active");
  recognition.start();
}

function takeSnapshot() {
  if (!state.cameraActive) {
    addMessage("pet", "先开启摄像头，我才能保存当前画面给视觉模型。");
    return;
  }
  const canvas = dom.canvas;
  state.snapshot = canvas.toDataURL("image/jpeg", 0.72);
  setMood("thinking", "已保存一帧画面。接入 Qwen-VL 等视觉模型后，我可以把它作为多模态上下文。");
  addMessage("pet", "当前画面快照已准备好。若配置了支持 vision 的 OpenAI 兼容接口，下一次提问会带上这张图。");
}

async function sendChat(rawText) {
  const text = rawText.trim();
  if (!text) return;
  dom.chatInput.value = "";
  registerInput("聊天输入", "thinking", "我在组织回复。");
  addMessage("user", text);

  let reply;
  try {
    reply = state.model.apiBase && state.model.apiKey && state.model.modelName
      ? await callModel(text)
      : localReply(text);
  } catch (error) {
    reply = `模型接口调用失败，我先用本地规则回答：${localReply(text)}`;
  }

  addMessage("pet", reply);
  setMood(reply.length > 52 ? "curious" : "cheer", reply.slice(0, 92));
  speak(reply.slice(0, 96));
}

function addMessage(role, text) {
  const item = document.createElement("div");
  item.className = `message ${role === "user" ? "user-message" : "pet-message"}`;
  item.textContent = text;
  dom.chatLog.appendChild(item);
  dom.chatLog.scrollTop = dom.chatLog.scrollHeight;
  state.messages.push({ role: role === "user" ? "user" : "assistant", content: text });
  if (state.messages.length > 12) {
    state.messages = state.messages.slice(-12);
  }
}

function localReply(text) {
  const sensorLine = `现在我的感知状态是：${getPresenceLabel()}，亮度 ${state.brightness ?? "未知"}，动作 ${state.motion ?? "未知"}，最近输入 ${state.lastAction}。`;
  if (/能做什么|功能|介绍|你是谁/.test(text)) {
    return `我是一个结合 BongoCat 输入同步思路的具身桌宠原型。当前能做本地摄像头状态感知、键鼠动作反馈、语音播报、语音输入和对话回复。${sensorLine}`;
  }
  if (/观察|看到|状态|在吗|我在/.test(text)) {
    return sensorLine;
  }
  if (/累|烦|压力|难受|焦虑|困/.test(text)) {
    return "我听到了。先把目标压小一点：现在只推进一个可见动作，比如完成一个页面、一次测试或一段说明。需要的话我可以每隔一会儿提醒你休息。";
  }
  if (/怎么做|方案|架构|实现/.test(text)) {
    return "建议按四层实现：BongoCat/Tauri 负责桌面窗口和输入事件，多模态感知层处理摄像头帧，LLM Agent 决定回复与动作，TTS/Live2D 层输出语音和表情。先做规则状态机，再替换为 Qwen-VL + DeepSeek。";
  }
  return `${sensorLine} 我会根据这些信号调整表情和回复。接入真实多模态模型后，可以把摄像头快照、你的文字和当前状态一起交给模型生成更自然的互动。`;
}

async function callModel(text) {
  const messages = [
    {
      role: "system",
      content:
        "你是一个中文具身AI桌面宠物。回复要短、温和、可执行。你可以引用本地传感状态，但不要声称看到了没有提供的信息。",
    },
    {
      role: "user",
      content: `传感状态：${getPresenceLabel()}；亮度=${state.brightness ?? "unknown"}；动作=${state.motion ?? "unknown"}；最近输入=${state.lastAction}`,
    },
    ...state.messages.slice(-6),
  ];

  const userContent = state.snapshot
    ? [
        { type: "text", text },
        { type: "image_url", image_url: { url: state.snapshot } },
      ]
    : text;
  messages.push({ role: "user", content: userContent });

  const response = await fetch(`${state.model.apiBase.replace(/\/$/, "")}/chat/completions`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${state.model.apiKey}`,
    },
    body: JSON.stringify({
      model: state.model.modelName,
      messages,
      temperature: 0.7,
      max_tokens: 220,
    }),
  });
  if (!response.ok) {
    throw new Error(`HTTP ${response.status}`);
  }
  const data = await response.json();
  return data.choices?.[0]?.message?.content?.trim() || "模型没有返回有效文本。";
}

function saveModelConfig() {
  state.model = {
    apiBase: dom.apiBase.value.trim(),
    modelName: dom.modelName.value.trim(),
    apiKey: dom.apiKey.value.trim(),
  };
  localStorage.setItem("project39-model", JSON.stringify(state.model));
  addMessage("pet", "模型设置已保存在本机浏览器。若接口支持跨域和 OpenAI 兼容格式，后续聊天会调用真实模型。");
}

function loadModelConfig() {
  try {
    const saved = JSON.parse(localStorage.getItem("project39-model") || "{}");
    state.model = { ...state.model, ...saved };
    dom.apiBase.value = state.model.apiBase;
    dom.modelName.value = state.model.modelName;
    dom.apiKey.value = state.model.apiKey;
  } catch {
    localStorage.removeItem("project39-model");
  }
}

function proactiveTick() {
  if (Date.now() - state.lastInputAt < 12000) return;
  if (state.cameraActive && state.brightness !== null && state.brightness < 54) {
    addMessage("pet", "环境偏暗，我会切到低打扰状态。需要继续学习的话，可以开一盏灯保护眼睛。");
    speak("环境偏暗，注意保护眼睛。");
    return;
  }
  if (state.cameraActive && state.faceCount === 0 && state.motion < 6) {
    setMood("sleepy", "你可能离开了一会儿，我先静静待命。");
  }
}

init();
