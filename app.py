import base64
import os
import streamlit as st


# Hàm chuyển đổi file ảnh local sang chuỗi Base64 hiển thị trực tiếp trên HTML
def get_image_base64(path):
  if os.path.exists(path):
    with open(path, "rb") as f:
      encoded = base64.b64encode(f.read()).decode("utf-8")
      ext = path.split(".")[-1].lower()
      mime = "image/png" if ext == "png" else "image/jpeg"
      return f"data:{mime};base64,{encoded}"
  return ""


player_b64 = get_image_base64("player.png")
monster_b64 = get_image_base64("monster.png")
bg_b64 = get_image_base64("background.png")

st.set_page_config(
    page_title="Temple Run: Tralalero vs Peppa", page_icon="🏃‍♂️", layout="centered"
)

st.title("🏃‍♂️ Temple Run: Chạy Trốn Heo Peppa")
st.markdown("""
* **Trái / Phải (← / → / A / D):** Đổi làn đường
* **Nhảy lên (↑ / W):** Nhảy qua bẫy gai / vật cản thấp
* **Trượt xuống (↓ / S):** Trượt cúi người né rào cản treo cao
""")

game_html = f"""
<!DOCTYPE html>
<html lang="vi">
<head>
    <meta charset="UTF-8">
    <title>Temple Run - Jump & Slide Edition</title>
    <style>
        body {{
            background-color: #0e1117;
            color: white;
            text-align: center;
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            margin: 0;
            padding: 0;
        }}
        canvas {{
            background: #111;
            display: block;
            margin: 0 auto;
            border-radius: 12px;
            box-shadow: 0 0 25px rgba(255, 75, 75, 0.4);
        }}
        .controls {{
            margin-top: 15px;
            display: flex;
            justify-content: center;
            gap: 10px;
            flex-wrap: wrap;
        }}
        .btn {{
            background-color: #ff4b4b;
            color: white;
            border: none;
            padding: 10px 20px;
            font-size: 16px;
            font-weight: bold;
            border-radius: 8px;
            cursor: pointer;
            box-shadow: 0 4px 10px rgba(0,0,0,0.5);
            transition: all 0.2s;
        }}
        .btn:hover {{
            background-color: #ff2222;
            transform: scale(1.05);
        }}
        .level-select {{
            margin-bottom: 10px;
        }}
        .level-btn {{
            background-color: #333;
            color: #fff;
            border: 2px solid #ff4b4b;
            padding: 8px 16px;
            margin: 0 5px;
            border-radius: 6px;
            cursor: pointer;
            font-weight: bold;
        }}
        .level-btn.active {{
            background-color: #ff4b4b;
            color: white;
        }}
    </style>
</head>
<body>

    <!-- Nhạc nền Vết Thương - Fishy -->
    <audio id="bgMusic" loop preload="auto">
        <source src="https://files.catbox.moe/k3b8x2.mp3" type="audio/mp3">
    </audio>

    <div class="level-select">
        <span style="font-weight:bold; margin-right:10px;">Chọn Cấp Độ:</span>
        <button class="level-btn active" id="lvl1" onclick="setLevel(1, 3.5, 90)">Cấp 1 (Dễ)</button>
        <button class="level-btn" id="lvl2" onclick="setLevel(2, 5.5, 70)">Cấp 2 (Vừa)</button>
        <button class="level-btn" id="lvl3" onclick="setLevel(3, 8.0, 50)">Cấp 3 (Khó)</button>
        <button class="level-btn" id="lvl4" onclick="setLevel(4, 11.5, 35)">Cấp 4 (Bá Khí)</button>
    </div>

    <canvas id="gameCanvas" width="600" height="500"></canvas>
    
    <div class="controls">
        <button class="btn" onclick="moveLeft()">◀ Trái</button>
        <button class="btn" onclick="jump()">▲ Nhảy (W)</button>
        <button class="btn" onclick="slide()">▼ Trượt (S)</button>
        <button class="btn" onclick="moveRight()">Phải ▶</button>
    </div>

    <script>
        const canvas = document.getElementById("gameCanvas");
        const ctx = canvas.getContext("2d");
        const bgMusic = document.getElementById("bgMusic");

        // Tải hình ảnh từ file
        const playerImg = new Image();
        playerImg.src = "{player_b64}";

        const monsterImg = new Image();
        monsterImg.src = "{monster_b64}";

        const bgImg = new Image();
        bgImg.src = "{bg_b64}";

        // Thiết lập game
        let currentLevel = 1;
        let gameSpeed = 3.5;
        let spawnRate = 90;
        
        let score = 0;
        let gameOver = false;
        let gameStarted = false;

        const lanesBottom = [160, 300, 440];
        const lanesTop = [260, 300, 340];

        let playerLane = 1; 
        let playerX = lanesBottom[playerLane];
        let playerY = 350;

        let isJumping = false;
        let jumpY = 0;
        let jumpVelocity = 0;
        let isSliding = false;
        let slideTimer = 0;

        let monsterLane = 1;
        let monsterX = lanesBottom[monsterLane];
        let monsterY = 440;

        let obstacles = [];
        let frameCount = 0;
        let roadOffset = 0;

        function setLevel(lvl, speed, rate) {{
            currentLevel = lvl;
            gameSpeed = speed;
            spawnRate = rate;
            document.querySelectorAll('.level-btn').forEach(btn => btn.classList.remove('active'));
            document.getElementById('lvl' + lvl).classList.add('active');
            if(gameStarted) resetGame();
        }}

        window.addEventListener("keydown", function(e) {{
            if (!gameStarted && (e.code === "Space" || e.code === "Enter")) {{
                startGame();
                return;
            }}
            if (gameOver && e.code === "Space") {{
                startGame();
                return;
            }}
            if (!gameOver && gameStarted) {{
                if (e.code === "ArrowLeft" || e.code === "KeyA") moveLeft();
                if (e.code === "ArrowRight" || e.code === "KeyD") moveRight();
                if (e.code === "ArrowUp" || e.code === "KeyW") jump();
                if (e.code === "ArrowDown" || e.code === "KeyS") slide();
            }}
        }});

        function startGame() {{
            gameStarted = true;
            resetGame();
        }}

        function moveLeft() {{
            if (playerLane > 0) playerLane--;
        }}

        function moveRight() {{
            if (playerLane < 2) playerLane++;
        }}

        function jump() {{
            if (!isJumping && !isSliding) {{
                isJumping = true;
                jumpVelocity = 14;
            }}
        }}

        function slide() {{
            if (!isJumping && !isSliding) {{
                isSliding = true;
                slideTimer = 25;
            }}
        }}

        function resetGame() {{
            score = 0;
            gameOver = false;
            obstacles = [];
            playerLane = 1;
            monsterLane = 1;
            gameStarted = true;
            isJumping = false;
            jumpY = 0;
            isSliding = false;
            
            // Phát nhạc nền
            bgMusic.currentTime = 0;
            bgMusic.play().catch(e => console.log("Cần bấm tương tác để phát nhạc"));
        }}

        function update() {{
            if (!gameStarted || gameOver) return;

            if (isJumping) {{
                jumpY += jumpVelocity;
                jumpVelocity -= 1;
                if (jumpY <= 0) {{
                    jumpY = 0;
                    isJumping = false;
                }}
            }}

            if (isSliding) {{
                slideTimer--;
                if (slideTimer <= 0) {{
                    isSliding = false;
                }}
            }}

            let targetPlayerX = lanesBottom[playerLane];
            playerX += (targetPlayerX - playerX) * 0.25;

            let targetMonsterX = lanesBottom[playerLane];
            monsterX += (targetMonsterX - monsterX) * 0.08; 

            roadOffset = (roadOffset + gameSpeed) % 40;

            frameCount++;
            if (frameCount % Math.floor(spawnRate) === 0) {{
                let lane = Math.floor(Math.random() * 3);
                let type = Math.floor(Math.random() * 3); 
                obstacles.push({{ lane: lane, progress: 0, type: type, passed: false }});
            }}

            for (let i = obstacles.length - 1; i >= 0; i--) {{
                let obs = obstacles[i];
                obs.progress += gameSpeed * 0.0035;

                if (obs.progress >= 0.65 && obs.progress <= 0.85) {{
                    if (obs.lane === playerLane) {{
                        let hit = false;
                        if (obs.type === 0) {{
                            if (jumpY < 30) hit = true;
                        }} else if (obs.type === 1) {{
                            if (!isSliding) hit = true;
                        }} else if (obs.type === 2) {{
                            if (jumpY < 20) hit = true;
                        }}

                        if (hit) {{
                            gameOver = true;
                            bgMusic.pause();
                        }}
                    }}
                }}

                if (obs.progress > 0.85 && !obs.passed) {{
                    score += 10 * currentLevel;
                    obs.passed = true;
                }}

                if (obs.progress >= 1.0) {{
                    obstacles.splice(i, 1);
                }}
            }}
        }}

        function drawTempleRoad() {{
            ctx.fillStyle = "#1b110a";
            ctx.fillRect(0, 0, canvas.width, 120);

            if (bgImg.complete && bgImg.naturalWidth !== 0) {{
                ctx.globalAlpha = 0.35;
                ctx.drawImage(bgImg, 0, 0, canvas.width, 180);
                ctx.globalAlpha = 1.0;
            }}

            ctx.fillStyle = "#8d6e63";
            ctx.beginPath();
            ctx.moveTo(220, 120);
            ctx.lineTo(380, 120);
            ctx.lineTo(540, 500);
            ctx.lineTo(60, 500);
            ctx.closePath();
            ctx.fill();

            ctx.strokeStyle = "#4e342e";
            ctx.lineWidth = 12;
            ctx.beginPath();
            ctx.moveTo(220, 120); ctx.lineTo(60, 500);
            ctx.moveTo(380, 120); ctx.lineTo(540, 500);
            ctx.stroke();

            ctx.strokeStyle = "#6d4c41";
            ctx.lineWidth = 3;
            for (let y = 120 + (roadOffset % 30); y < 500; y += 30) {{
                let p = (y - 120) / (500 - 120);
                let xLeft = 220 - p * 160;
                let xRight = 380 + p * 160;
                ctx.beginPath();
                ctx.moveTo(xLeft, y);
                ctx.lineTo(xRight, y);
                ctx.stroke();
            }}
        }}

        function drawObstacle(obs) {{
            let p = obs.progress;
            let currentY = 120 + p * (500 - 120);
            let currentX = lanesTop[obs.lane] + p * (lanesBottom[obs.lane] - lanesTop[obs.lane]);
            let size = 15 + p * 45;

            if (obs.type === 0) {{
                ctx.fillStyle = "#5d4037";
                ctx.beginPath();
                ctx.arc(currentX, currentY, size, 0, Math.PI * 2);
                ctx.fill();
                ctx.strokeStyle = "#3e2723";
                ctx.lineWidth = 3;
                ctx.stroke();
            }} else if (obs.type === 1) {{
                ctx.fillStyle = "#ff9800";
                ctx.fillRect(currentX - size * 1.2, currentY - size * 1.2, size * 2.4, size * 0.6);
                ctx.fillStyle = "#4e342e";
                ctx.fillRect(currentX - size * 1.1, currentY - size * 0.6, size * 0.2, size * 1.2);
                ctx.fillRect(currentX + size * 0.9, currentY - size * 0.6, size * 0.2, size * 1.2);
                ctx.fillStyle = "#fff";
                ctx.font = "bold 12px Arial";
                ctx.textAlign = "center";
                ctx.fillText("CÚI (S)", currentX, currentY - size * 0.8);
            }} else {{
                ctx.fillStyle = "#c62828";
                for (let i = -2; i <= 2; i++) {{
                    ctx.beginPath();
                    ctx.moveTo(currentX + i * 8, currentY + size / 2);
                    ctx.lineTo(currentX + i * 8 + 4, currentY - size / 2);
                    ctx.lineTo(currentX + i * 8 + 8, currentY + size / 2);
                    ctx.fill();
                }}
                ctx.fillStyle = "#fff";
                ctx.font = "bold 12px Arial";
                ctx.textAlign = "center";
                ctx.fillText("NHẢY (W)", currentX, currentY + size);
            }}
        }}

        function draw() {{
            ctx.clearRect(0, 0, canvas.width, canvas.height);

            drawTempleRoad();

            if (!gameStarted) {{
                ctx.fillStyle = "rgba(0, 0, 0, 0.75)";
                ctx.fillRect(0, 0, canvas.width, canvas.height);
                ctx.fillStyle = "#ff4b4b";
                ctx.font = "bold 28px Arial";
                ctx.textAlign = "center";
                ctx.fillText("TEMPLE RUN: TRALALERO VS PEPPA", canvas.width / 2, 180);
                ctx.fillStyle = "white";
                ctx.font = "16px Arial";
                ctx.fillText("Phím ↑ / W: Nhảy | Phím ↓ / S: Trượt cúi", canvas.width / 2, 230);
                ctx.fillText("Nhấn phím Cách (Space) để Bắt đầu", canvas.width / 2, 280);
                return;
            }}

            for (let obs of obstacles) {{
                drawObstacle(obs);
            }}

            // Quái vật Peppa
            if (monsterImg.complete && monsterImg.naturalWidth !== 0) {{
                ctx.drawImage(monsterImg, monsterX - 45, monsterY - 40, 90, 80);
            }} else {{
                ctx.fillStyle = "pink";
                ctx.fillRect(monsterX - 35, monsterY - 35, 70, 70);
            }}

            // Player Tralalero
            let drawPlayerY = playerY - jumpY;
            let drawPlayerHeight = isSliding ? 35 : 65;
            let drawPlayerWidth = isSliding ? 70 : 60;

            if (playerImg.complete && playerImg.naturalWidth !== 0) {{
                ctx.drawImage(playerImg, playerX - drawPlayerWidth / 2, drawPlayerY - drawPlayerHeight / 2, drawPlayerWidth, drawPlayerHeight);
            }} else {{
                ctx.fillStyle = "#0288d1";
                ctx.fillRect(playerX - drawPlayerWidth / 2, drawPlayerY - drawPlayerHeight / 2, drawPlayerWidth, drawPlayerHeight);
            }}

            ctx.fillStyle = "white";
            ctx.font = "bold 20px Arial";
            ctx.textAlign = "left";
            ctx.fillText("Điểm: " + score, 20, 35);
            ctx.fillText("Cấp độ: " + currentLevel, 20, 65);

            if (isJumping) ctx.fillText("🚀 ĐANG NHẢY!", 20, 95);
            if (isSliding) ctx.fillText("💨 ĐANG TRƯỜNG!", 20, 95);

            if (gameOver) {{
                ctx.fillStyle = "rgba(0, 0, 0, 0.85)";
                ctx.fillRect(0, 0, canvas.width, canvas.height);
                ctx.fillStyle = "#ff4b4b";
                ctx.font = "bold 34px Arial";
                ctx.textAlign = "center";
                ctx.fillText("BẠN ĐÃ BỊ HEO PEPPA BẮT!", canvas.width / 2, 200);
                ctx.fillStyle = "white";
                ctx.font = "22px Arial";
                ctx.fillText("Tổng điểm: " + score, canvas.width / 2, 250);
                ctx.fillText("Nhấn phím Cách (Space) để Chơi lại", canvas.width / 2, 310);
            }}
        }}

        function loop() {{
            update();
            draw();
            requestAnimationFrame(loop);
        }}

        loop();
    </script>
</body>
</html>
"""

st.components.v1.html(game_html, height=640)
