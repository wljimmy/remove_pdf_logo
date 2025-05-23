#!/bin/bash

# PDF Logo 删除工具执行脚本
# 用于交互式收集参数并执行Python程序

# 确保脚本在当前目录执行
cd "$(dirname "$0")"

# 检查Python3是否安装
if ! command -v python3 &> /dev/null; then
    echo "错误: 未找到Python 3。请先安装Python 3。"
    read -p "按回车键退出..."
    exit 1
fi

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
NC='\033[0m' # 无颜色

echo -e "${GREEN}=== PDF Logo 删除工具 ===${NC}"
echo ""

# 获取输入PDF文件路径
while true; do
    echo -n "请输入PDF文件路径: "
    read input_pdf
    
    if [ -f "$input_pdf" ]; then
        break
    else
        echo -e "${RED}错误: 文件不存在或不是有效文件。请重新输入。${NC}"
    fi
done

# 获取输出PDF文件路径
while true; do
    echo -n "请输入输出文件路径 (默认: ${input_pdf%.*}_no_logo.pdf): "
    read output_pdf
    
    if [ -z "$output_pdf" ]; then
        output_pdf="${input_pdf%.*}_no_logo.pdf"
    fi
    
    if [ -f "$output_pdf" ]; then
        echo -n "文件已存在。是否覆盖? (y/n): "
        read confirm
        if [ "$confirm" = "y" ] || [ "$confirm" = "Y" ]; then
            break
        fi
    else
        break
    fi
done

# 获取图像保存目录
echo -n "请输入保存提取图像的目录 (默认: ./pdf_images): "
read image_dir

if [ -z "$image_dir" ]; then
    image_dir="./pdf_images"
fi

# 创建目录（如果不存在）
mkdir -p "$image_dir"

echo ""
echo -e "${YELLOW}参数确认:${NC}"
echo -e "  输入PDF: ${GREEN}$input_pdf${NC}"
echo -e "  输出PDF: ${GREEN}$output_pdf${NC}"
echo -e "  图像目录: ${GREEN}$image_dir${NC}"
echo ""

echo -n "是否继续? (y/n): "
read confirm

if [ "$confirm" != "y" ] && [ "$confirm" != "Y" ]; then
    echo "操作已取消。"
    read -p "按回车键退出..."
    exit 0
fi

echo ""
echo -e "${GREEN}开始处理PDF...${NC}"
echo ""

# 执行Python脚本
python3 pdf_logo_remover.py -i "$input_pdf" -o "$output_pdf" -d "$image_dir"

echo ""
echo -e "${GREEN}处理完成!${NC}"

# 打开保存目录（如果有图像）
if [ -d "$image_dir" ] && [ "$(ls -A "$image_dir")" ]; then
    echo -n "是否打开保存图像的目录? (y/n): "
    read open_dir
    
    if [ "$open_dir" = "y" ] || [ "$open_dir" = "Y" ]; then
        open "$image_dir"
    fi
fi

read -p "按回车键退出..."
exit 0    