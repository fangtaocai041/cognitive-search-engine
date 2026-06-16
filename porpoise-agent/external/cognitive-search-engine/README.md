"""
⚠️ 重要提示: porpoise-agent/external/cognitive-search-engine/

此目录是 cognitive-search-engine 的完整副本（约 344 KB Python 代码）。

问题:
  - 代码重复: 与 workspace 根目录的 cognitive-search-engine 内容一致
  - 维护风险: 更新主项目时此副本不会同步

建议解决方案:
  Option A (推荐): 删除此目录, 改为 git submodule
    cd porpoise-agent
    rm -rf external/cognitive-search-engine
    git submodule add https://github.com/fangtaocai041/cognitive-search-engine.git external/cognitive-search-engine

  Option B: 删除此目录, 修改 import 路径指向 workspace 根目录
    # 在 porpoise-agent 的代码中:
    import sys
    sys.path.insert(0, "../cognitive-search-engine")

  Option C: 保留但添加 CI 检查确保不产生 drift
    # .github/workflows/validate.yml 中添加:
    # python -c "assert open('external/cognitive-search-engine/VERSION').read() == open('../cognitive-search-engine/VERSION').read()"
"""

DUPLICATED_CODE_WARNING = """
This is a copy of cognitive-search-engine. 
Use git submodule instead to avoid code drift.
"""
