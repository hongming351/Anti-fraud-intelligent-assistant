import os
import json
from multimodal_processor import analyze_image

def batch_test(image_folder):
    results = []
    for filename in os.listdir(image_folder):
        if filename.lower().endswith(('.png', '.jpg', '.jpeg')):
            path = os.path.join(image_folder, filename)
            print(f"正在分析: {filename}")
            result = analyze_image(path)
            results.append({
                "image": filename,
                "result": result
            })
    # 保存结果到 JSON
    with open("test_results.json", "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    print("批量测试完成，结果已保存到 test_results.json")
    return results

if __name__ == "__main__":
    batch_test("test_images")