"""Tests for strategy_classifier — rule-based classify_query()."""
import pytest

from app.services.strategy_classifier import classify_query


class TestClassifyQueryEmpty:
    """Empty/blank input returns 'none'."""

    def test_empty_string(self):
        assert classify_query("") == "none"

    def test_none_input(self):
        assert classify_query(None) == "none"

    def test_whitespace_only(self):
        assert classify_query("   ") == "none"


class TestClassifyQueryMultiQueryComparison:
    """Comparison patterns → multi_query."""

    def test_vs(self):
        assert classify_query("React vs Vue") == "multi_query"

    def test_vs_dot(self):
        assert classify_query("Python vs. Java performance") == "multi_query"

    def test_difference_between(self):
        assert classify_query("What is the difference between TCP and UDP?") == "multi_query"

    def test_differences_between(self):
        assert classify_query("differences between arrays and linked lists") == "multi_query"

    def test_pros_and_cons(self):
        assert classify_query("pros and cons of microservices architecture") == "multi_query"

    def test_compare(self):
        assert classify_query("compare REST and GraphQL APIs") == "multi_query"

    def test_comparison(self):
        assert classify_query("a comparison of sorting algorithms") == "multi_query"

    def test_versus(self):
        assert classify_query("Docker versus Kubernetes for deployment") == "multi_query"

    def test_cn_duibi(self):
        assert classify_query("对比React和Vue的性能") == "multi_query"

    def test_cn_qubie(self):
        assert classify_query("TCP和UDP的区别") == "multi_query"

    def test_cn_youquedian(self):
        assert classify_query("微服务架构的优缺点") == "multi_query"

    def test_cn_haishi(self):
        assert classify_query("用Python还是Java") == "multi_query"

    def test_cn_bijiao(self):
        assert classify_query("比较两种排序算法") == "multi_query"


class TestClassifyQueryMultiQueryShort:
    """Short/ambiguous queries → multi_query."""

    def test_single_word(self):
        assert classify_query("React") == "multi_query"

    def test_two_words(self):
        assert classify_query("React hooks") == "multi_query"

    def test_three_words(self):
        assert classify_query("Python web frameworks") == "multi_query"

    def test_four_words(self):
        assert classify_query("best sorting algorithm performance") == "multi_query"

    def test_short_cn(self):
        assert classify_query("依赖注入") == "multi_query"

    def test_short_cn_8chars(self):
        assert classify_query("动态规划贪心算法") == "multi_query"

    def test_not_short_with_question_mark(self):
        """Short query with ? should NOT be classified as short → may be hyde."""
        result = classify_query("React?")
        # Single word with ? is not 5+ words, so falls to none
        assert result == "none"


class TestClassifyQueryHydeInterrogative:
    """Interrogative patterns → hyde."""

    def test_what_is(self):
        assert classify_query("What is dependency injection in Spring?") == "hyde"

    def test_what_are(self):
        assert classify_query("What are the benefits of using TypeScript?") == "hyde"

    def test_how_does(self):
        assert classify_query("How does garbage collection work in Java?") == "hyde"

    def test_how_do(self):
        assert classify_query("How do you implement a binary search tree?") == "hyde"

    def test_how_to(self):
        assert classify_query("How to set up a CI/CD pipeline with GitHub Actions?") == "hyde"

    def test_explain(self):
        assert classify_query("Explain the observer pattern with examples") == "hyde"

    def test_describe(self):
        assert classify_query("Describe the MVC architecture pattern") == "hyde"

    def test_why(self):
        assert classify_query("Why does Python use the GIL?") == "hyde"

    def test_define(self):
        assert classify_query("Define polymorphism in object-oriented programming") == "hyde"

    def test_tell_me_about(self):
        assert classify_query("Tell me about Kubernetes pod networking") == "hyde"

    def test_cn_shenme_shi(self):
        assert classify_query("什么是依赖注入？") == "hyde"

    def test_cn_ruhe(self):
        assert classify_query("如何实现二叉搜索树") == "hyde"

    def test_cn_weishenme(self):
        assert classify_query("为什么Python使用GIL") == "hyde"

    def test_cn_zenme(self):
        assert classify_query("怎么配置CI/CD流水线") == "hyde"

    def test_cn_jieshi(self):
        assert classify_query("解释观察者模式的工作原理") == "hyde"

    def test_cn_miaoshu(self):
        assert classify_query("描述MVC架构模式") == "hyde"

    def test_cn_jieshao(self):
        assert classify_query("介绍Kubernetes的网络模型") == "hyde"


class TestClassifyQueryHydeQuestionMark:
    """Long questions ending with ? → hyde."""

    def test_long_en_question(self):
        assert classify_query("Can you show me how to implement this pattern correctly?") == "hyde"

    def test_long_cn_question(self):
        assert classify_query("这个设计模式在实际项目中如何应用？") == "hyde"

    def test_short_en_question_not_hyde(self):
        """Short question with ? but <5 words → none (not enough context for hyde)."""
        assert classify_query("React hooks?") == "none"


class TestClassifyQueryNoneFallback:
    """Fallback to none for specific/command-style queries."""

    def test_file_path(self):
        assert classify_query("src/components/App.tsx line 42 error handling") == "none"

    def test_specific_lookup(self):
        assert classify_query("useState return type in React eighteen") == "none"

    def test_command_style(self):
        assert classify_query("list all files in the knowledge directory recursively") == "none"


class TestClassifyQueryCaseInsensitive:
    """EN patterns should be case-insensitive."""

    def test_what_is_uppercase(self):
        assert classify_query("WHAT IS dependency injection?") == "hyde"

    def test_vs_mixed_case(self):
        assert classify_query("React VS Angular") == "multi_query"

    def test_explain_titlecase(self):
        assert classify_query("Explain the observer pattern in detail please") == "hyde"


class TestClassifyQueryPriority:
    """Comparison takes priority over interrogative."""

    def test_comparison_overrides_interrogative(self):
        # "What is the difference between" has both interrogative and comparison
        assert classify_query("What is the difference between X and Y?") == "multi_query"

    def test_short_overrides_none(self):
        # 2-word query without patterns → short → multi_query
        assert classify_query("data structures") == "multi_query"
