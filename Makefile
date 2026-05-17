fmt:
	terraform fmt -recursive

validate:
	terraform validate

test:
	python -m pytest tests/ -v

plan:
	terraform plan
