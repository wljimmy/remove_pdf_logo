import fitz  # PyMuPDF
import cv2
import numpy as np
from PIL import Image
from io import BytesIO
import os
import argparse
from tqdm import tqdm
import time

def multi_scale_template_matching(pdf_path, template_path, min_scale=0.5, max_scale=1.5, steps=10, threshold=0.8, pages=None):
    """
    使用多尺度模板匹配检测PDF中的Logo，适应不同大小的Logo
    
    参数:
    min_scale (float): 最小缩放比例
    max_scale (float): 最大缩放比例
    steps (int): 缩放步数
    """
    logo_positions = []
    
    try:
        # 加载模板图片
        template = cv2.imread(template_path, 0)
        if template is None:
            raise ValueError(f"无法加载模板图片: {template_path}")
            
        doc = fitz.open(pdf_path)
        
        # 确定要处理的页面范围
        if pages is None:
            pages = range(len(doc))
        else:
            pages = [p for p in pages if 0 <= p < len(doc)]
        
        print(f"开始在 {len(pages)} 个页面中多尺度检测Logo...")
        page_iter = tqdm(pages, desc="页面检测进度", unit="页")
        
        for page_num in page_iter:
            page = doc[page_num]
            page_iter.set_postfix_str(f"正在处理第 {page_num+1} 页")
            
            # 将PDF页面转换为图像
            try:
                pix = page.get_pixmap()
                img_bytes = pix.tobytes("png")
                img_pil = Image.open(BytesIO(img_bytes)).convert("L")  # 转换为灰度图
                img_cv = np.array(img_pil)
                
                # 多尺度匹配
                found = None
                match_results = []
                
                # 生成缩放比例列表
                scales = np.linspace(min_scale, max_scale, steps)
                
                # 对每个缩放比例进行匹配
                scale_iter = tqdm(scales, desc="尺度搜索", unit="尺度", leave=False)
                for scale in scale_iter:
                    scale_iter.set_postfix_str(f"当前缩放: {scale:.2f}")
                    
                    # 调整模板大小
                    resized = cv2.resize(template, 
                                        (int(template.shape[1] * scale), 
                                         int(template.shape[0] * scale)))
                    
                    if resized.shape[0] > img_cv.shape[0] or resized.shape[1] > img_cv.shape[1]:
                        continue  # 模板大于原图，跳过
                    
                    # 执行模板匹配
                    result = cv2.matchTemplate(img_cv, resized, cv2.TM_CCOEFF_NORMED)
                    (minVal, maxVal, minLoc, maxLoc) = cv2.minMaxLoc(result)
                    
                    # 记录匹配结果
                    if maxVal >= threshold:
                        match_results.append({
                            'scale': scale,
                            'max_val': maxVal,
                            'location': maxLoc,
                            'template_size': (resized.shape[1], resized.shape[0])
                        })
                
                # 处理匹配结果
                for match in match_results:
                    scale = match['scale']
                    maxVal = match['max_val']
                    (startX, startY) = match['location']
                    (tW, tH) = match['template_size']
                    
                    # 计算实际矩形区域
                    endX = startX + tW
                    endY = startY + tH
                    
                    logo_positions.append({
                        'page_num': page_num,
                        'rect': [startX, startY, endX, endY],
                        'confidence': maxVal,
                        'scale': scale
                    })
                
                # 更新进度条后缀显示匹配数量
                if match_results:
                    page_iter.set_postfix_str(f"第 {page_num+1} 页找到 {len(match_results)} 个匹配")
                
                time.sleep(0.05)  # 为了演示效果
                
            except Exception as e:
                print(f"警告: 处理第 {page_num+1} 页时出错: {str(e)}")
        
        doc.close()
        
        # 显示检测结果摘要
        if logo_positions:
            page_matches = len(set(p['page_num'] for p in logo_positions))
            total_matches = len(logo_positions)
            scale_min = min(p['scale'] for p in logo_positions)
            scale_max = max(p['scale'] for p in logo_positions)
            print(f"检测完成！在 {page_matches} 个页面中找到 {total_matches} 个Logo匹配")
            print(f"匹配尺度范围: {scale_min:.2f}x - {scale_max:.2f}x")
        else:
            print("检测完成！未找到匹配的Logo")
            
    except Exception as e:
        print(f"Logo检测失败: {pdf_path}, 错误: {str(e)}")
    
    return logo_positions

def remove_logo_from_pdf(input_pdf, output_pdf, logo_info_list, method="cover"):
    """
    从PDF中删除或覆盖Logo
    """
    try:
        doc = fitz.open(input_pdf)
        
        # 按页面分组处理
        pages_to_process = sorted(list(set(info['page_num'] for info in logo_info_list)))
        total_pages = len(pages_to_process)
        
        print(f"开始处理PDF...")
        page_iter = tqdm(pages_to_process, desc="页面处理进度", unit="页")
        
        for page_num in page_iter:
            page = doc[page_num]
            page_logos = [info for info in logo_info_list if info['page_num'] == page_num]
            
            page_iter.set_postfix_str(f"第 {page_num+1} 页处理 {len(page_logos)} 个Logo")
            
            for logo_info in page_logos:
                if method == "delete":
                    # 尝试直接删除对象
                    if 'xref' in logo_info:
                        try:
                            page.delete_image(logo_info['xref'])
                        except Exception as e:
                            print(f"警告: 无法删除页面 {page_num+1} 的Logo: {str(e)}")
                            method = "cover"
                    else:
                        print(f"警告: 页面 {page_num+1} 的Logo无法直接删除（缺少XRef信息），将使用覆盖模式")
                        method = "cover"
                
                if method == "cover":
                    # 用白色矩形覆盖Logo区域
                    rect = logo_info.get('rect')
                    if rect:
                        rect = fitz.Rect(*rect)
                        page.draw_rect(rect, color=(1, 1, 1), fill=(1, 1, 1), overlay=True)
            
            time.sleep(0.05)  # 为了演示效果
        
        # 保存修改后的PDF
        print("正在保存修改后的PDF...")
        doc.save(output_pdf)
        doc.close()
        
        return True, f"成功处理: {input_pdf}"
    except Exception as e:
        return False, f"处理失败: {input_pdf}, 错误: {str(e)}"

def main():
    parser = argparse.ArgumentParser(description='PDF多页面Logo批量删除工具')
    parser.add_argument('-i', '--input', required=True, help='输入PDF文件路径')
    parser.add_argument('-o', '--output', required=True, help='输出PDF文件路径')
    parser.add_argument('-t', '--template', required=True, help='Logo模板图片路径')
    parser.add_argument('--threshold', type=float, default=0.8, help='匹配阈值(0-1)，默认0.8')
    parser.add_argument('--method', choices=['cover', 'delete'], default='cover', help='处理方式：覆盖(cover)或删除(delete)，默认覆盖')
    parser.add_argument('--pages', type=int, nargs='+', help='指定处理的页面（例如：--pages 0 1 2），默认处理所有页面')
    
    # 多尺度匹配参数
    parser.add_argument('--min-scale', type=float, default=0.5, help='最小缩放比例，默认0.5')
    parser.add_argument('--max-scale', type=float, default=1.5, help='最大缩放比例，默认1.5')
    parser.add_argument('--scale-steps', type=int, default=10, help='缩放步数，默认10')
    
    args = parser.parse_args()
    
    # 检查输入文件是否存在
    if not os.path.exists(args.input):
        print(f"错误: 输入文件 '{args.input}' 不存在")
        return
    
    if not os.path.exists(args.template):
        print(f"错误: 模板图片 '{args.template}' 不存在")
        return
    
    # 获取PDF总页数
    try:
        doc = fitz.open(args.input)
        total_pdf_pages = len(doc)
        doc.close()
        
        print(f"正在处理 PDF: {args.input}")
        print(f"总页数: {total_pdf_pages}")
        if args.pages:
            print(f"指定处理页数: {len(args.pages)}")
        else:
            print(f"处理所有页面")
            
    except Exception as e:
        print(f"无法获取PDF页数: {str(e)}")
        total_pdf_pages = "未知"
    
    # 开始计时
    start_time = time.time()
    
    # 多尺度检测Logo位置
    logo_positions = multi_scale_template_matching(
        args.input, 
        args.template,
        min_scale=args.min_scale,
        max_scale=args.max_scale,
        steps=args.scale_steps,
        threshold=args.threshold,
        pages=args.pages
    )
    
    if not logo_positions:
        print("未检测到匹配的Logo，处理终止")
        return
    
    # 处理PDF
    print("\n" + "="*50)
    success, message = remove_logo_from_pdf(
        args.input, 
        args.output, 
        logo_positions, 
        method=args.method
    )
    
    # 结束计时
    end_time = time.time()
    elapsed_time = end_time - start_time
    
    # 显示最终结果
    print("\n" + "="*50)
    if success:
        print(f"✅ 处理成功!")
        print(f"- 输入文件: {args.input}")
        print(f"- 输出文件: {args.output}")
        print(f"- 处理页数: {len(set(p['page_num'] for p in logo_positions))}")
        print(f"- 删除Logo数量: {len(logo_positions)}")
        print(f"- 处理耗时: {elapsed_time:.2f}秒")
    else:
        print(f"❌ 处理失败: {message}")

if __name__ == "__main__":
    main()    