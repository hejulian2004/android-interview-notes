# 题目维护检查表

在 data/questions.json 新增一个对象，至少填写：唯一 id、title、category、kind、priority、scope、evidence、answer、pitfall、followup、references、answer_provenance、review_status、updated_at。

来源题的 evidence 每项包括 source_id 和 observed_variant，source_id 必须指向 admitted 来源。补充练习 evidence 为空，不能暗示某家公司问过。

回答要包含成立条件；延伸追问不能冒充原题。技术 reference 使用 references.json 的键。新增后运行 build.py、validate.py 和 unittest。
