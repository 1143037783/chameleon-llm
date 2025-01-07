import os
import re
import sys
import json
import openai

# add the parent directory to the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utilities import *
from demos import prompt_policy, prompt_kr, prompt_sg, prompt_qg, prompt_pg, prompt_cl,prompt_tv,prompt_rl

# OpenAI
openai.api_key = os.getenv("OPENAI_API_KEY")
print(openai.api_key)

# OpenAI
bing_api_key = os.getenv("BING_API_KEY")
print(bing_api_key)

class solver:

    def __init__(self, args):
        # arguments
        for key, value in vars(args).items():
            setattr(self, key, value)
        # for chameleon
        if self.model == "chameleon":
            self.use_caption = False # disabled by default, could be enabled by the policy

        # external arguments
        self.api_key = openai.api_key
        self.examples, self.pids = self.load_data()

    def load_data(self):
        # load test data
        pid_splits = json.load(open(os.path.join(self.data_root, "pid_splits.json")))
        _examples = json.load(open(os.path.join(self.data_root, "problems.json")))

        examples = {pid: _examples[pid] for pid in pid_splits[self.test_split]}
        pids = list(examples.keys())

        # update metadata
        for pid, example in examples.items():
            image = example["image"]
            split = example["split"]
            if image:
                example["image_file"] = os.path.join(self.data_root, "images", split, pid, image)
            else:
                example["image_file"] = ""

        # limit the number of test examples
        if self.test_number > 0:
            if self.test_number < len(pids):
                pids = pids[:self.test_number]
                examples = {key: value for key, value in examples.items() if key in pids}

        # load caption data
        if os.path.exists(self.caption_file):
            captions = json.load(open(self.caption_file))["captions"]
            for pid in examples:
                examples[pid]['caption'] = captions[pid] if pid in captions else ""

        # load ocr data
        if os.path.exists(self.ocr_file):
            ocrs = json.load(open(self.ocr_file))["texts"]
            for pid in examples:
                examples[pid]['ocr'] = ocrs[pid] if pid in ocrs else []
        

        return examples, pids


    def get_question_text(self):
        if "question_text" in self.cache:
            return self.cache["question_text"] 
        
        # context
        text_context = self.cache["example"]["hint"]
        image_context = self.cache["example"]["caption"] if self.use_caption else ""
        context = " ".join([text_context, image_context]).strip()

        # option
        choices = self.cache["example"]["choices"]
        inds = ["A", "B", "C", "D", "E"]
        choice_list = [f"({inds[i]}) {choices[i]}" for i in range(len(choices))]
        option = " ".join(choice_list)

        # question text
        question = self.cache["example"]["question"]
        if context != "":
            question_text = f"{question}\n\nContext: {context}\n\nOptions: {option}"
        else:
            question_text = f"{question}\n\nOptions: {option}"

        self.cache["question_text"] = question_text
        return question_text

    def get_metadata(self):
        if "metadata" in self.cache:
            return self.cache["metadata"]
        
        # extract metadata
        metadata = {}
        example = self.cache["example"]
        metadata["has_image"] = True if example["image"] else False
        metadata["grade"] = int(example["grade"].replace("grade", ""))
        metadata["subject"] = example["subject"]
        metadata["topic"] = example["topic"]
        metadata["category"] = example["category"]
        metadata["skill"] = example["skill"]

        self.cache["metadata"] = metadata
        return metadata

    def build_prompt_for_policy(self):
        # get the example
        question_text = self.get_question_text()
        metadata = self.get_metadata()

        # build the prompt
        demo_prompt = prompt_policy.prompt.strip() # demo prompt
        test_prompt = f"Question: {question_text}\n\nMetadata: {metadata}\n\nModules: " # test prompt
        full_prompt = demo_prompt + "\n\n" + test_prompt # full prompt

        return test_prompt, full_prompt

    def predict_modules(self):
        # get the module input
        test_prompt, full_prompt = self.build_prompt_for_policy()
        messages=[
            {"role": "user", "content": full_prompt},
        ]

        # execute the module
        modules = get_chat_response(messages, self.api_key, self.policy_engine, self.policy_temperature, self.policy_max_tokens)
        modules = self.update_modules(modules)

        # update the cache
        self.cache["modules:input"] = test_prompt
        self.cache["modules:output"] = modules
        return modules

    def update_modules(self, _modules):
        # default modules
        default_modules = ["solution_generator", "answer_generator"]
        
        try:
            modules = eval(_modules.lower().strip())
            assert modules[-2:] == default_modules
        except:
            modules = default_modules

        return modules
    
    def image_captioner(self):
        # get the module input
        image_file = self.cache["example"]["image_file"]
        response = self.cache["response"] if "response" in self.cache else ""

        # excute the module 
        if "caption" in self.cache["example"]:
            caption = self.cache["example"]["caption"]
        else:
            if not os.path.exists(image_file):
                caption = ""
            else:
                # TODO: run the image captioner model on the fly
                caption = "" 

        # update the response cache
        if caption != "":
            response += f"\n\nImage caption: {caption}"
            response = response.strip()

        # update the cache
        self.cache["response"] = response
        self.cache["image_captioner:input"] = image_file
        self.cache["image_captioner:output"] = caption
        return image_file, caption
    
    def text_detector(self):
        # get the module input
        image_file = self.cache["example"]["image_file"]
        response = self.cache["response"] if "response" in self.cache else ""

        # excute the module 
        texts = []
        if "ocr" in self.cache["example"]:
            try:
                ocr = eval(self.cache["example"]["ocr"])
                if len(ocr) > 0:
                    texts = [(t[0], t[1]) for t in ocr] # (coordinates, text)
            except:
                pass
        else:
            if not os.path.exists(image_file):
                texts = []
            else:
                # TODO: run the image captioner model on the fly
                texts = []

        # update the response cache
        if len(texts) > 0:
            response += f"\n\nDetected text in the image: {texts}"
            response = response.strip()

        # update the cache
        self.cache["response"] = response
        self.cache["text_detector:input"] = image_file
        self.cache["text_detector:output"] = texts
        return image_file, texts
    
    def knowledge_retrieval(self):
        # get the example
        question_text = self.get_question_text()
        metadata = self.get_metadata()
        response = self.cache["response"] if "response" in self.cache else ""

        # build the prompt
        demo_prompt = prompt_kr.prompt.strip() # demo prompt
        if response != "":
            test_prompt = f"Question: {question_text}\n\nMetadata: {metadata}\n\n{response}\n\nKnowledge:\n"
        else:
            test_prompt = f"Question: {question_text}\n\nMetadata: {metadata}\n\nKnowledge:\n" # test prompt
        full_prompt = demo_prompt + "\n\n" + test_prompt # full prompt

        messages=[
            {"role": "user", "content": full_prompt},
        ]

        # execute the module
        knowledge = get_chat_response(messages, self.api_key, self.kr_engine, self.kr_temperature, self.kr_max_tokens)

        # update the response cache
        if knowledge != "" and knowledge != None:
            response += f"\n\nKnowledge:\n{knowledge}"
            response = response.strip()

        # update the cache
        self.cache["response"] = response
        self.cache["knowledge_retrieval:input"] = test_prompt
        self.cache["knowledge_retrieval:output"] = knowledge
        return test_prompt, knowledge

    def query_generator(self):
        # get the example
        question_text = self.get_question_text()
        metadata = self.get_metadata()
        response = self.cache["response"] if "response" in self.cache else ""

        # demo prompt
        demo_prompt = prompt_qg.prompt.strip() 
        # test prompt
        if response != "":
            test_prompt = f"Question: {question_text}\n\nMetadata: {metadata}\n\n{response}\n\nSearch Query: "
        else:
            test_prompt = f"Question: {question_text}\n\nMetadata: {metadata}\n\nSearch Query: "
        # full prompt
        full_prompt = demo_prompt + "\n\n" + test_prompt
        messages=[
            {"role": "user", "content": full_prompt},
        ]

        # execute the module
        query = get_chat_response(messages, self.api_key, self.qg_engine, self.qg_temperature, self.qg_max_tokens)
        if query == "" or query == None:
            query = None

        # update the cache
        self.cache["query"] = query
        self.cache["query_generator:input"] = test_prompt
        self.cache["query_generator:output"] = query
        return test_prompt, query

    def bing_search(self):
        # get the module input
        endpoint = self.endpoint
        count = self.search_count
        query = self.cache["query"] if "query" in self.cache else None
        response = self.cache["response"] if "response" in self.cache else ""

        # excute the module (call the Bing Search API and get the responses)
        if query != None and query != "":
            result = call_bing_search(endpoint, bing_api_key, query, count)
        else:
            result = None
        responses = parse_bing_result(result)

        if len(responses) > 0 and responses[0] != "":
            response += f"\n\nBing search response: {responses}"
            response = response.strip()

        # update the cache
        self.cache["response"] = response
        self.cache["bing_search:input"] = query
        self.cache["bing_search:output"] = responses
        return query, responses

    def build_prompt_for_sg_chameleon(self):
        # get the input
        question_text = self.get_question_text()
        metadata = self.get_metadata()
        response = self.cache["response"] if "response" in self.cache else ""

        # build the prompt
        demo_prompt = prompt_sg.prompt_chameleon.strip() # WARNING: this is the prompt for chameleon
        if response != "":
            test_prompt = f"Question: {question_text}\n\nMetadata: {metadata}\n\n{response}\n\nSolution: "
        else:
            test_prompt = f"Question: {question_text}\n\nMetadata: {metadata}\n\nSolution: "
        full_prompt = demo_prompt + "\n\n" + test_prompt # full prompt
        return test_prompt, full_prompt

    def build_prompt_for_sg_cot(self):
        question = self.cache["example"]["question"]
        choices = self.cache["example"]["choices"]
        hint = self.cache["example"]["hint"]
        caption = self.cache["example"]["caption"]

        # demo prompt
        demo_prompt = prompt_sg.prompt_cot.strip() # WARNING: this is the prompt for COT
    
        # option
        inds = ["A", "B", "C", "D", "E"]
        choice_list = [f"({inds[i]}) {choices[i]}" for i in range(len(choices))]
        option = " ".join(choice_list)

        # context
        context = hint.strip() 
        if self.use_caption and caption != "":
            context += f" Image: {caption}"
    
        #  test prompt
        if context != "":
            test_prompt = f"Question: {question}\n\nContext: {context}\n\nOptions: {option}\n\nSolution: "
        else:
            test_prompt = f"Question: {question}\n\nOptions: {option}\n\nSolution: "

        full_prompt = demo_prompt + "\n\n" + test_prompt
        return test_prompt, full_prompt

    def row_lookup(self):
        # get the module input
        question = self.cache["example"]["question"]
        table = self.cache["example"]["table"]
        context = self.cache["example"]["context"] if "context" in self.cache["example"] else ""
        row_num = self.cache["example"]["row_num"]
        column_num = self.cache["example"]["column_num"]
        cell_num = row_num * column_num

        # if row_num <=3 or cell_num <= 12:
        if row_num <= self.rl_row_threshold or cell_num <= self.rl_cell_threshold:
            test_prompt = None
            simple_table = table

        else:
            demo_prompt = prompt_rl.prompt.strip()
            # test_prompt = f"Question: {question}\n\nTable:\n\n{table}\n\nSimplified Table:\n"
            if context != "":
                test_prompt = f"Question: {question}\n\nTable:\n{table}\n\n{context}\n\nSimplified Table:\n"
            else:
                test_prompt = f"Question: {question}\n\nTable:\n{table}\n\nSimplified Table:\n"

            full_prompt = demo_prompt + "\n\n" + test_prompt
            messages = [
                {"role": "user", "content": full_prompt},
            ]
            # execute the module
            if self.rl_cand == 1:
                simple_table = get_chat_response(messages, self.api_key, self.rl_engine, self.rl_temperature,
                                                 self.rl_max_tokens)
            else:
                simple_tables = get_chat_response(messages, self.api_key, self.rl_engine, self.rl_temperature,
                                                  self.rl_max_tokens, self.rl_cand)
                simple_table = max(simple_tables, key=simple_tables.count)

        # update the cache
        self.cache["example"]["table"] = simple_table  # update the table!!
        self.cache["row_lookup:input"] = test_prompt
        self.cache["row_lookup:output"] = simple_table
        return test_prompt, simple_table

    def column_lookup(self):
        # get the module input
        question = self.cache["example"]["question"]
        table = self.cache["example"]["table"]
        context = self.cache["example"]["context"] if "context" in self.cache["example"] else ""
        row_num = self.cache["example"]["row_num"]
        column_num = self.cache["example"]["column_num"]
        cell_num = row_num * column_num

        # if column_num <= 2 or cell_num <= 12:
        if column_num <= self.cl_col_threshold or cell_num <= self.cl_cell_threshold:
            test_prompt = None
            simple_table = table

        else:
            demo_prompt = prompt_cl.prompt.strip()
            # test_prompt = f"Question: {question}\n\nTable:\n\n{table}\n\nSimplified Table:\n"
            if context != "":
                test_prompt = f"Question: {question}\n\nTable:\n\n{table}\n\n{context}\n\nSimplified Table:\n"
            else:
                test_prompt = f"Question: {question}\n\nTable:\n\n{table}\n\nSimplified Table:\n"
            full_prompt = demo_prompt + "\n\n" + test_prompt
            messages = [
                {"role": "user", "content": full_prompt},
            ]
            # execute the module
            simple_table = get_chat_response(messages, self.api_key, self.cl_engine, self.cl_temperature,
                                             self.cl_max_tokens)

        # update the cache
        self.cache["example"]["table"] = simple_table  # update the table!!
        self.cache["column_lookup:input"] = test_prompt
        self.cache["column_lookup:output"] = simple_table
        return test_prompt, simple_table

    def table_verbalizer(self):
        # get the module input
        question = self.cache["example"]["question"]
        table = self.cache["example"]["table"]
        context = self.cache["example"]["context"] if "context" in self.cache["example"] else ""

        demo_prompt = prompt_tv.prompt.strip()
        # test_prompt = f"Question: {question}\n\nTable:\n\n{table}\n\nTable description:\n"
        if context != "":
            test_prompt = f"Question: {question}\n\nTable:\n\n{table}\n\n{context}\n\nTable description:\n"
        else:
            test_prompt = f"Question: {question}\n\nTable:\n\n{table}\n\nTable description:\n"
        full_prompt = demo_prompt + "\n\n" + test_prompt
        messages = [
            {"role": "user", "content": full_prompt},
        ]

        # execute the module
        verbalization = get_chat_response(messages, self.api_key, self.tv_engine, self.tv_temperature,
                                          self.tv_max_tokens)
        context += f"\n\nTable description: {verbalization}".strip()

        # update the cache
        self.cache["example"]["context"] = context
        self.cache["table_verbalizer:input"] = test_prompt
        self.cache["table_verbalizer:output"] = verbalization
        return test_prompt, verbalization

    def build_prompt_for_pg(self):
        question = self.cache["example"]["question"]
        unit = self.cache["example"]["unit"]
        choices = self.cache["example"]["choices"]
        table = self.cache["example"]["table"]
        table_title = self.cache["example"]["table_title"]
        context = self.cache["example"]["context"] if "context" in self.cache["example"] else ""

        if choices:
            demo_prompt = prompt_pg.prompt_choice.strip()
        else:
            demo_prompt = prompt_pg.prompt_free.strip()

        if table_title:
            instruction = f"Read the following table regarding {table_title} and then write Python code to answer a question:"
        else:
            instruction = "Read the following table and then write Python code to answer a question:"

        if unit:
            question += f" (Unit: {unit})"
        if choices:
            question += f" Please select from the following options: {choices}."

        if choices:
            solution = "# Python Code, return 'ans'. Make sure that 'ans' is a string selected from the options in the question"
        else:
            solution = "# Python Code, return 'ans'. Make sure that 'ans' is a number"

        if context != "":
            test_prompt = f"{instruction}\n\n{table}\n\n{context}\n\n{question}\n\n{solution}"
        else:
            test_prompt = f"{instruction}\n\n{table}\n\n{question}\n\n{solution}"

        full_prompt = demo_prompt + "\n\n" + test_prompt
        return test_prompt, full_prompt

    def program_generator(self):
        # get the module input
        test_prompt, full_prompt = self.build_prompt_for_pg()
        messages = [
            {"role": "user", "content": full_prompt},
        ]

        # excute the module
        program = get_chat_response(messages, self.api_key, self.pg_engine, self.pg_temperature, self.pg_max_tokens)

        # update the cache
        self.cache["program"] = program
        self.cache["program_generator:input"] = test_prompt
        self.cache["program_generator:output"] = program
        return test_prompt, program

    def _verify_program(self, program):
        # check if the program is valid
        if not isinstance(program, str):
            return False
        if isinstance(program, str):
            if "ans =" not in program:
                return False
        _output = safe_execute(program)
        if _output in (None, "", [], {}):
            return False
        return True

    def program_verifier(self):
        if "program" in self.cache:
            program = self.cache["program"]
        else:
            return None, False

        # excute the module
        success = self._verify_program(program)

        # update the cache
        self.cache["program_verifier:output"] = success
        return program, success

    def program_generator_and_verifier(self):
        # get the module input
        patience = self.pv_patience
        test_prompt, full_prompt = self.build_prompt_for_pg()
        messages = [
            {"role": "user", "content": full_prompt},
        ]

        # excute the module
        program = None
        success = False
        count = 0
        while count < patience and not success:
            if self.pg_temperature < 0.1 and count > 0:
                _temperature = min(self.pg_temperature + 0.1, 1.0)
            else:
                _temperature = self.pg_temperature
            program = get_chat_response(messages, self.api_key, self.pg_engine, _temperature, self.pg_max_tokens)
            success = self._verify_program(program)
            count += 1
            # if not success:
            #     print(program)

        # update the cache
        self.cache["program"] = program
        self.cache["program_generator_and_verifier:input"] = test_prompt
        self.cache["program_generator_and_verifier:output"] = program
        return test_prompt, program

    def program_executor(self):
        if "program" in self.cache:
            program = self.cache["program"]
        else:
            return None, False

        # excute the module
        ans = safe_execute(program)

        # update the cache
        self.cache["program_executor:output"] = ans
        return program, ans

    def solution_generator(self):
        # get the module input
        if self.model == "chameleon":
            test_prompt, full_prompt = self.build_prompt_for_sg_chameleon()
        else:
            test_prompt, full_prompt = self.build_prompt_for_sg_cot()

        messages=[
            {"role": "user", "content": full_prompt},
        ]

        # excute the module
        success = False
        patience = self.sg_patience
        count = 0
        while count < patience and not success:
            if self.sg_temperature < 0.1 and count > 0:
                _temperature = min(self.sg_temperature + 0.1, 1.0)
            else:
                _temperature = self.sg_temperature

            solution = get_chat_response(messages, self.api_key, self.sg_engine, _temperature, self.sg_max_tokens)
            # print(f"Solution: {solution}")

            pattern = re.compile(r"[Tt]he answer is ([A-Z])") # "The answer is XXXXX.",
            res = pattern.findall(solution)
            if len(res) > 0:
                success = True
            count += 1

        # update the cache
        self.cache["solution"] = solution
        self.cache["solution_generator:input"] = test_prompt
        self.cache["solution_generator:output"] = solution
        return test_prompt, solution
    
    def answer_generator(self):
        # get the module input
        output = self.cache["solution"]
        options = self.cache["example"]["choices"]
        inds = ["A", "B", "C", "D", "E"]

        # excute the module
        success = False
        if output:
            pattern = re.compile(r"[Tt]he answer is ([A-Z])") # "The answer is A.",
            res = pattern.findall(output)
            if len(res) > 0:
                ans = res[0] # "A"
                if ans in inds[:len(options)]:
                    success = True
                    prediction = options[inds.index(ans)]

        if not success:
            prediction = normalize_prediction_scienceqa(output, options)

        # update the cache
        self.cache["prediction"] = prediction
        self.cache["answer_generator:input"] = output
        self.cache["answer_generator:output"] = prediction
        return output, prediction
