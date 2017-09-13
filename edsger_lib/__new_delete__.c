#include <stdio.h>
#include <stdlib.h>

typedef struct node{
	long long addr;
	struct node *next;
} mem_node;

mem_node *head;
short initiated = 0;

short _init_mem_nodes(){
	if(!initiated){
		head = NULL;
		initiated = 1;
	}
	return sizeof(mem_node);
}

void _do_new(long long address, mem_node * p){
	p->addr = address;
	if (head == NULL){
		head = p;
		p = NULL;
		head->next = NULL;
	}
	else{
		p->next = head;
		head = p;
		p = NULL;
	}
	return;
}

void _do_delete(long long address){
	mem_node *p;
	p = head;
	while (p != NULL){
		if (p->addr == address) break;
		p = p->next;
	}
	if (p == NULL){
		printf("\nDeleting something that doesn't exist!\n");
		printf("Exiting...\n");
		exit(42);
	}
	else{
		if (head == p){
			head = head->next;
			p = NULL;
		}
		else{
			mem_node *q;
			q = head;
			while(q->next != p) q = q->next;
			q->next = p->next;
			p = NULL;
			q = NULL;
		}
		return;
	}
}