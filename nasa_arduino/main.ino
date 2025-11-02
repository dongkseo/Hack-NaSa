#include <WiFiS3.h>
#include <PubSubClient.h>
#include <IRremote.h>

// ------------------------
// 1. WiFi 및 MQTT 설정
// ------------------------
const char* ssid = "WIFI_SSID";           // Wi-Fi 네트워크 이름
const char* password = "WIFI_PASSWORD";   // Wi-Fi 비밀번호
const char* mqtt_server = "MQTT_BROKER_IP"; // MQTT 브로커 주소 (예: Raspberry Pi, Mosquitto)
const int mqtt_port = 1883;

// 에어컨 제어 명령을 받을 토픽
#define COMMAND_TOPIC "home/ac/control" 

WiFiClient espClient;
PubSubClient client(espClient);

// ------------------------
// 2. IR 발신 설정
// ------------------------
const int IR_SEND_PIN = 3;

// ------------------------
// 3. LG 에어컨 코드 (확보한 RAW 데이터 입력)
// ------------------------
// LG 에어컨 ON 코드 (실제 데이터로 대체해야 합니다)
// 예시: 실제 IR 리시버로 캡처한 RAW 데이터를 여기에 입력
unsigned int lg_on_code[] = {
  8800, 4400, 550, 550, 550, 1650, 550, 550, 550, 1650, 550, 550, 550, 550, 550, 1650,
  550, 550, 550, 550, 550, 1650, 550, 1650, 550, 550, 550, 1650, 550, 1650, 550, 550
};
int lg_on_len = sizeof(lg_on_code) / sizeof(lg_on_code[0]);

// LG 에어컨 OFF 코드 (실제 데이터로 대체해야 합니다)
unsigned int lg_off_code[] = {
  8800, 4400, 550, 550, 550, 1650, 550, 550, 550, 1650, 550, 1650, 550, 550, 550, 1650,
  550, 550, 550, 550, 550, 1650, 550, 1650, 550, 550, 550, 1650, 550, 1650, 550, 550
};
int lg_off_len = sizeof(lg_off_code) / sizeof(lg_off_code[0]);


// ------------------------
// 4. MQTT 메시지 수신 시 처리 함수 (Callback)
// ------------------------
void callback(char* topic, byte* payload, unsigned int length) {
  Serial.print("Message received [");
  Serial.print(topic);
  Serial.print("]: ");
  
  // 수신된 페이로드를 문자열로 변환
  String message;
  for (int i = 0; i < length; i++) {
    message += (char)payload[i];
  }
  message.toUpperCase(); // 대소문자 구분 없이 처리

  if (message == "ON") {
    Serial.println("-> Sending AC ON signal!");
    // RAW 데이터 전송: (데이터 배열, 길이, 주파수 38kHz)
    IrSender.sendRaw(lg_on_code, lg_on_len, 38);

  } else if (message == "OFF") {
    Serial.println("-> Sending AC OFF signal!");
    IrSender.sendRaw(lg_off_code, lg_off_len, 38);
    
  } else {
    Serial.println("-> Unknown command.");
  }
}

// ------------------------
// 5. 연결 재시도 함수
// ------------------------
void reconnect() {
  while (!client.connected()) {
    Serial.print("Attempting MQTT connection...");
    // 클라이언트 ID는 임의로 지정
    if (client.connect("ArduinoClient-AC")) {
      Serial.println("connected");
      // 명령 토픽을 구독
      client.subscribe(COMMAND_TOPIC);
    } else {
      Serial.print("failed, rc=");
      Serial.print(client.state());
      Serial.println(" trying again in 5 seconds");
      delay(5000);
    }
  }
}

// ------------------------
// 6. Setup 및 Loop
// ------------------------
void setup() {
  Serial.begin(115200);
  IrSender.begin(IR_SEND_PIN); // IR 발신기 초기화

  // Wi-Fi 연결
  Serial.print("Connecting to ");
  Serial.println(ssid);
  WiFi.begin(ssid, password);

  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }

  Serial.println("");
  Serial.println("WiFi connected");
  Serial.print("IP address: ");
  Serial.println(WiFi.localIP());

  // MQTT 설정
  client.setServer(mqtt_server, mqtt_port);
  client.setCallback(callback);
}

void loop() {
  if (!client.connected()) {
    reconnect(); // 연결 끊어지면 재접속 시도
  }
  client.loop(); // MQTT 클라이언트 통신 유지
}