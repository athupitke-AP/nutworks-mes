import paho.mqtt.client as mqtt
import json, time, math, random

BROKER = "localhost"
PORT = 1883
TOPIC = "nutworks/production/sensors"

client = mqtt.Client()
client.connect(BROKER, PORT)
print(f"Connected to MQTT broker")
print(f"Publishing to: {TOPIC}")
print("Press Ctrl+C to stop\n")

t = 0
while True:
    t += 1
    roaster_temp = 180 + math.sin(t / 30) * 20 + random.uniform(-2, 2)
    silo1 = max(0, 5000 - (t * 0.5))
    silo2 = max(0, 4200 - (t * 0.4))
    silo3 = max(0, 3800 - (t * 0.3))
    bags  = 45 + random.randint(-3, 3) if roaster_temp > 160 else 0
    tank1 = max(0, 75 - (t * 0.01))
    tank2 = max(0, 60 - (t * 0.008))

    payload = {
        "roaster_temp_c":    round(roaster_temp, 1),
        "roaster_running":   roaster_temp > 160,
        "silo1_weight_kg":   round(silo1, 1),
        "silo2_weight_kg":   round(silo2, 1),
        "silo3_weight_kg":   round(silo3, 1),
        "coater_speed_rpm":  35 + random.randint(-2, 2),
        "coater_running":    roaster_temp > 160,
        "tank1_level_pct":   round(tank1, 1),
        "tank2_level_pct":   round(tank2, 1),
        "bags_per_min":      bags,
        "boxes_completed":   t // 10,
        "line_running":      roaster_temp > 160,
        "timestamp":         time.time()
    }

    client.publish(TOPIC, json.dumps(payload))
    print(f"T={t:04d} | Roaster={roaster_temp:.1f}C | "
        f"Bags={bags}/min | Tank1={tank1:.0f}% | Tank2={tank2:.0f}%")
    time.sleep(2)