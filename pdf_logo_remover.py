import sys
import subprocess
import os
import argparse
import time
import hashlib
from io import BytesIO
from PIL import Image
import fitz  # PyMuPDF
from tqdm import tqdm

def install_dependencies():
    """检查并安装所有依赖库"""
    required_packages = {
        'fitz': 'pymupdf',
        'PIL': 'pillow',
        'tqdm': 'tqdm'
    }
    
    missing_packages = []
    
    # 检查缺失的包
    for module, package in required_packages.items():
        try:
            __import__(module)
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        print(f"检测到缺少依赖库: {', '.join(missing_packages)}")
        print("正在尝试自动安装...")
        
        try:
            # 使用pip3安装缺失的包
            subprocess.check_call([sys.executable, "-m", "pip", "install", *missing_packages])
            print(f"✅ 依赖库安装成功")
            return True
        except subprocess.CalledProcessError as e:
            print(f"❌ 依赖库安装失败: {e}")
            print("请尝试手动安装:")
            print(f"pip3 install {' '.join(missing_packages)}")
            return False
    else:
        print("✅ 所有依赖库已安装")
        return True

# 在导入任何可能缺失的库之前先检查依赖
if __name__ == "__main__":
    if not install_dependencies():
        print("依赖安装失败，程序无法继续运行")
        sys.exit(1)

def extract_images_from_pdf(pdf_path):
    """
    从PDF中提取所有图像组件
    
    返回:
    图像列表，每个图像包含:
    - xref: 图像在PDF中的引用编号
    - page_num: 所在页面
    - width: 宽度
    - height: 高度
    - image_data: 图像二进制数据
    - image_hash: 图像哈希值（用于去重）
    """
    images = []
    
    try:
        doc = fitz.open(pdf_path)
        
        print(f"开始从PDF中提取图像...")
        page_iter = tqdm(range(len(doc)), desc="页面扫描进度", unit="页")
        
        for page_num in page_iter:
            page = doc[page_num]
            image_list = page.get_images(full=True)
            
            if image_list:
                page_iter.set_postfix_str(f"第 {page_num+1} 页找到 {len(image_list)} 个图像")
                
                for image_index, img in enumerate(image_list, start=1):
                    xref = img[0]
                    base_image = doc.extract_image(xref)
                    image_bytes = base_image["image"]
                    image_ext = base_image["ext"]
                    
                    # 计算图像哈希值（用于去重）
                    image_hash = hashlib.md5(image_bytes).hexdigest()
                    
                    # 获取图像尺寸
                    try:
                        img_pil = Image.open(BytesIO(image_bytes))
                        width, height = img_pil.size
                    except:
                        width, height = 0, 0
                    
                    # 记录图像信息
                    images.append({
                        'xref': xref,
                        'page_num': page_num,
                        'width': width,
                        'height': height,
                        'size': len(image_bytes),
                        'image_data': image_bytes,
                        'image_hash': image_hash,
                        'extension': image_ext
                    })
            
            time.sleep(0.01)  # 为了演示效果
        
        doc.close()
        
        print(f"✅ 图像提取完成，共找到 {len(images)} 个图像组件")
        
        return images
        
    except Exception as e:
        print(f"图像提取失败: {pdf_path}, 错误: {str(e)}")
        return []

def merge_duplicate_images(images):
    """
    合并重复的图像
    
    返回:
    去重后的图像列表，每个图像包含额外的 'occurrences' 字段，表示该图像出现的次数
    """
    unique_images = {}
    
    for image in images:
        img_hash = image['image_hash']
        
        if img_hash in unique_images:
            unique_images[img_hash]['occurrences'] += 1
            unique_images[img_hash]['pages'].append(image['page_num'])
        else:
            image_copy = image.copy()
            image_copy['occurrences'] = 1
            image_copy['pages'] = [image['page_num']]
            unique_images[img_hash] = image_copy
    
    # 转换为列表并按出现次数排序
    result = list(unique_images.values())
    result.sort(key=lambda x: x['occurrences'], reverse=True)
    
    print(f"合并重复图像后，剩余 {len(result)} 个唯一图像")
    
    return result

def display_images_for_selection(images, output_dir=None):
    """
    显示图像供用户选择
    
    返回:
    用户选择的图像列表
    """
    if not images:
        print("没有可选择的图像")
        return []
    
    print("\n" + "="*50)
    print("以下是PDF中提取的图像组件：")
    
    # 创建临时目录保存图像（如果需要）
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)
    
    # 显示图像列表
    for i, image in enumerate(images):
        pages_str = ', '.join([str(p + 1) for p in image['pages']])
        size_kb = image['size'] / 1024
        print(f"{i+1}. 图像 #{image['xref']} ({image['width']}x{image['height']}px, {size_kb:.1f}KB)")
        print(f"   出现次数: {image['occurrences']}, 所在页面: {pages_str}")
        
        # 保存图像（如果指定了输出目录）
        if output_dir:
            image_filename = f"image_{i+1}.{image['extension']}"
            image_path = os.path.join(output_dir, image_filename)
            
            with open(image_path, "wb") as img_file:
                img_file.write(image['image_data'])
            
            print(f"   保存路径: {image_path}")
        
        print("-" * 50)
    
    # 用户选择
    while True:
        selection = input("\n请输入要作为Logo删除的图像编号（用逗号分隔，如 1,3,5），或输入 'all' 删除全部，输入 'q' 退出: ")
        
        if selection.lower() == 'q':
            return []
        
        if selection.lower() == 'all':
            return images
        
        try:
            selected_indices = [int(x.strip()) - 1 for x in selection.split(',') if x.strip()]
            valid_indices = [i for i in selected_indices if 0 <= i < len(images)]
            
            if not valid_indices:
                print("无效的选择，请重新输入")
                continue
            
            if len(valid_indices) < len(selected_indices):
                print("忽略了无效的选择")
            
            selected_images = [images[i] for i in valid_indices]
            return selected_images
            
        except ValueError:
            print("输入格式错误，请使用数字和逗号")

def remove_selected_images_from_pdf(input_pdf, output_pdf, images_to_remove):
    """
    从PDF中删除选定的图像
    """
    if not images_to_remove:
        print("没有选择要删除的图像")
        return False, "未选择任何图像"
    
    try:
        doc = fitz.open(input_pdf)
        
        # 按页面分组处理
        pages_to_process = sorted(list(set(info['page_num'] for info in images_to_remove)))
        total_images = len(images_to_remove)
        
        print(f"\n开始从PDF中删除 {total_images} 个图像组件...")
        page_iter = tqdm(pages_to_process, desc="页面处理进度", unit="页")
        
        removed_count = 0
        
        for page_num in page_iter:
            page = doc[page_num]
            page_images = [info for info in images_to_remove if info['page_num'] == page_num]
            
            page_iter.set_postfix_str(f"第 {page_num+1} 页删除 {len(page_images)} 个图像")
            
            for image_info in page_images:
                xref = image_info['xref']
                
                try:
                    # 尝试删除图像
                    page.delete_image(xref)
                    removed_count += 1
                except Exception as e:
                    print(f"警告: 无法删除页面 {page_num+1} 的图像 #{xref}: {str(e)}")
            
            time.sleep(0.01)  # 为了演示效果
        
        # 保存修改后的PDF
        print("正在保存修改后的PDF...")
        doc.save(output_pdf)
        doc.close()
        
        return True, f"成功删除 {removed_count}/{total_images} 个图像组件"
    except Exception as e:
        return False, f"处理失败: {input_pdf}, 错误: {str(e)}"

def main():
    parser = argparse.ArgumentParser(description='PDF图像提取与Logo删除工具')
    parser.add_argument('-i', '--input', required=True, help='输入PDF文件路径')
    parser.add_argument('-o', '--output', required=True, help='输出PDF文件路径')
    parser.add_argument('-d', '--dir', help='保存图像的目录')
    
    args = parser.parse_args()
    
    # 检查输入文件是否存在
    if not os.path.exists(args.input):
        print(f"错误: 输入文件 '{args.input}' 不存在")
        return
    
    # 提取图像（不再直接保存）
    images = extract_images_from_pdf(args.input)
    
    if not images:
        print("PDF中未找到图像组件")
        return
    
    # 合并重复图像
    unique_images = merge_duplicate_images(images)
    
    # 让用户选择Logo图像（保存图像到指定目录）
    selected_images = display_images_for_selection(unique_images, args.dir)
    
    if not selected_images:
        print("未选择任何图像，程序终止")
        return
    
    # 确认用户选择
    print("\n" + "="*50)
    print(f"您选择了以下 {len(selected_images)} 个图像组件作为Logo:")
    for i, img in enumerate(selected_images):
        pages_str = ', '.join([str(p + 1) for p in img['pages']])
        print(f"{i+1}. 图像 #{img['xref']} ({img['width']}x{img['height']}px), 出现 {img['occurrences']} 次, 页面: {pages_str}")
    
    confirm = input("\n确定要从PDF中删除这些图像吗？(y/n): ")
    if confirm.lower() != 'y':
        print("操作已取消")
        return
    
    # 删除选定的图像
    print("\n" + "="*50)
    success, message = remove_selected_images_from_pdf(args.input, args.output, selected_images)
    
    # 显示最终结果
    print("\n" + "="*50)
    if success:
        print(f"✅ 处理成功!")
        print(f"- 输入文件: {args.input}")
        print(f"- 输出文件: {args.output}")
        print(f"- 删除图像数量: {message}")
    else:
        print(f"❌ 处理失败: {message}")

if __name__ == "__main__":
    main()    